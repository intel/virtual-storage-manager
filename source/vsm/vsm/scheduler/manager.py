# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# pylint: disable=W0703
# pylint: disable=R0912
# pylint: disable=R0914

"""
Scheduler Service
"""

import random
import time
from oslo.config import cfg
import datetime
import time
from vsm import db
from vsm import exception
from vsm import flags
from vsm import manager
from vsm import utils
from vsm.openstack.common import excutils
from vsm.openstack.common import importutils
from vsm.openstack.common import log as logging
from vsm.openstack.common.notifier import api as notifier
from vsm.openstack.common import timeutils
from vsm.openstack.common.rpc import common as rpc_exc
from vsm.conductor import rpcapi as conductor_rpcapi
from vsm.agent import rpcapi as agent_rpc
from vsm.conductor import api as conductor_api
from vsm.agent import cephconfigparser
from vsm.agent.crushmap_parser import CrushMap
from vsm.exception import *
from vsm.manifest.parser import ManifestParser
LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class SchedulerManager(manager.Manager):
    """Chooses a host to create storages."""

    RPC_API_VERSION = '1.2'

    def __init__(self, service_name=None, *args, **kwargs):
        #if not scheduler_driver:
        #    scheduler_driver = FLAGS.scheduler_driver
        #self.driver = importutils.import_object(scheduler_driver)
        super(SchedulerManager, self).__init__(*args, **kwargs)
        self._conductor_rpcapi = conductor_rpcapi.ConductorAPI()
        self._agent_rpcapi = agent_rpc.AgentAPI()
        #TODO change the use of conductor api to rpcapi.
        self._conductor_api = conductor_api.API()

    def init_host(self):
        LOG.info('init_host in manager ')

    def test_service(self, context, body=None):
        return {'key': 'test_service in scheduler'}

    def list_storage_pool(self, context):
        res = self._conductor_driver.list_storage_pool(context)
        LOG.info('scheduler/manager.py conductor value %s' % res)
        return res

    def get_storage_group_list(self, context):
        res = self._conductor_rpcapi.get_storage_group_list(context)
        LOG.info('scheduler/manager.py get_storage_group_list values %s' % res)
        return res

    def present_storage_pools(self, context, body=None):
        LOG.info('scheduler/manager.py present_storage_pools')
        return self._agent_rpcapi.present_storage_pools(context, body)

    def revoke_storage_pool(self, context, id):
        LOG.info('scheduler/manager.py revoke_storage_pool')
        self._agent_rpcapi.revoke_storage_pool(context, id)

    def create_storage_pool(self, context, body=None,cluster_id = None):
        LOG.info('scheduler/manager.py create_storage_pool')
        active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
        LOG.info('sync call to host = %s' % active_monitor['host'])
        body['cluster_id'] = active_monitor['cluster_id']

        pool_ref = db.pool_get_by_name(context,
                                       body['name'],
                                       body['cluster_id'])
        if body.has_key('size'):
            replication_factor = body['size']
            zone_cnt = len(db.zone_get_all(context))
            factor_flag = True
            message = ''
            if zone_cnt > 1 and replication_factor > zone_cnt:
                factor_flag = False
                message = "4004 - replication_factor of %s error:replica count greater than number of zones in Storage Group-loss of zone may result in data loss" % body['name']
                LOG.error(message)
            if zone_cnt <= 1:
                host_cnt = db.init_node_count_by_status(context,status='Active')
                if replication_factor > host_cnt:
                    factor_flag = False
                    message = "4005 - replication_factor of %s error:replica count greater than number of host in Storage Group-loss of host may resultin data loss" % body['name']
                    LOG.error(message)

            if not factor_flag:
                res = "pool "+ body['name'] + ":%s"%message
                return {'message':res}
        if not pool_ref:
            self._agent_rpcapi.create_storage_pool(context, body)#TODO need to specify host?
            #pool_id = self._agent_rpcapi.get_pool_id_by_name(context,
            #                body['name'], active_monitor['host'])
            #body['pool_id'] = pool_id
            #body['status'] = 'running'
            #pool_ref = db.pool_create(context, body)

            ## If it's created by periodic tasks.
            ## Update the new ones.
            #if pool_ref['tag'] == 'SYSTEM':
            #    db.pool_update_by_name(context,
            #                           body['name'],
            #                           body['cluster_id'],
            #                           body)
            res = "pool "+ body['name'] + "created"
        else:
            LOG.error("4003 - Pool %s has alreadey existed." % body['name'])
            try:
                raise StorageGroupAddFailed
            except Exception, e:
                LOG.error("%s: %s" %(e.code, e.message))
            res = "pool "+ body['name'] + "'s name repeated"
        return {'message':res}

    def get_server_list(self, context):
        res = self._conductor_rpcapi.get_server_list(context)
        LOG.info('scheduler/manager.py get_server_list values %s' % res)
        return res

    def _update_server_list_status(self,
                                   context,
                                   server_list,
                                   status):
        """Update the server list's status."""
        #TODO delete self._conductor_api which call conductor api.py.
        for server in server_list:
            self._conductor_api.init_node_update_status_by_id(context,
                                                              server['id'],
                                                              status)

    def _select_monitor(self, context, server_list):
        """Select on monitor to do jobs."""
        # Clean old configuration files and data.
        # Find one monitor to do this job.
        # Just monitor node can do this job.
        monitor_list = [x for x in server_list if x['is_monitor']]

        if len(monitor_list) == 0:
            LOG.error('Can not find monitor_list')
            try:
                raise MonitorAddFailed
            except Exception, e:
                LOG.error("%s: %s" %(e.code, e.message))

        monitor_default_size = 3
        if len(monitor_list) < monitor_default_size:
            LOG.error('For reliability, it is suggested to have at least %s monitors.'%monitor_default_size)
            self._update_server_list_status(context,
                                            server_list,
                                            "Warn: monitors < %s"%monitor_default_size)

        LOG.info(' monitor_list = %s' % monitor_list)
        if len(monitor_list) == 1:
            idx = 0
        else:
            idx = random.randint(0, len(monitor_list)-1)
        LOG.info(' select monitor = %d' % idx)
        job_server = monitor_list[idx]
        return job_server

    def _get_ceph_config(self, context):
        server_list = db.init_node_get_all(context)
        active_server_list = [x for x in server_list if x['status'] == "Active"]
        idx = random.randint(0, len(active_server_list)-1)
        active_server = active_server_list[idx]
        return self._agent_rpcapi.get_ceph_config(context,
                                                  active_server['host'])

    def _sync_config_from_host(self, context, host):
        # This function should not be used anymore.
        # We haved add sync function for every save_conf of cephconfigparser.
        return True

    def _start_add(self, context, host_id):
        server = self._conductor_api.init_node_get_by_id(context, host_id)
        LOG.info("server status before add role %s " % server['status'])
        if "available" in server['status']:
            self._conductor_api.init_node_update(context, host_id,
                {"status": "running", "type": ""})
        else:
            self._conductor_api.init_node_update(context, host_id,
                {"status": "running"})

    def _start_remove(self, context, host_id):
        self._conductor_api.init_node_update(context, host_id,
             {"status": "removing"})

    def _start_stop(self, context, host_id):
        self._conductor_api.init_node_update(context, host_id,
             {"status": "stopping"})

    def _start_start(self, context, host_id):
        self._conductor_api.init_node_update(context, host_id,
             {"status": "starting"})

    def _add_success(self, context, host_id, role):
        server = self._conductor_api.init_node_get_by_id(context, host_id)
        current_roles = [x.strip() for x in server['type'].split(",") if len(x.strip())]
        if not role in current_roles:
            current_roles.append(role)
        role_type = ",".join(current_roles)
        self._conductor_api.init_node_update(context, host_id,
             {"type": role_type, "status": "Active"})

    def _remove_success(self, context, host_id, role, is_unavail=False):
        LOG.info("host: %s  remove %s success!!" % (host_id, role))
        server = self._conductor_api.init_node_get_by_id(context, host_id)

        # If this server has been deleted from db.
        if not server:
            return

        current_roles = [x.strip() for x in server['type'].split(",") if len(x.strip())]
        new_roles = [x for x in current_roles if role != x]
        role_type = ",".join(new_roles)
        if len(new_roles):
            status = "Active"
        else:
            status = "available"
        if is_unavail:
            status = 'unavailable'
            # remove the server from the DB
            if len(new_roles) == 0:
                val = {"type": role_type, "status": status, 'deleted':1}
            else:
                val = {"type": role_type, "status": status}
        else:
            val = {"type": role_type, "status": status}
        self._conductor_api.init_node_update(context, host_id, val)

    def _add_or_remove_failed(self, context, host_id, role, is_unavail=False):
        server = self._conductor_api.init_node_get_by_id(context, host_id)
        current_roles = [x.strip() for x in server['type'].split(",") if x.strip()]
        if len(current_roles):
            status = "Active"
        else:
            status = "available"
        if is_unavail:
            status = 'unavailable'

        self._conductor_api.init_node_update(context, host_id,
             {"status": status})

    def _get_active_monitor(self, context, beyond_list=None, cluster_id = None):
        def __is_in(host):
            if not beyond_list:
                return False

            for ser in beyond_list:
                if ser['host'] == host:
                    return True
            return False
        if cluster_id:
            server_list = db.init_node_get_by_cluster_id(context, cluster_id)
        else:
            server_list = db.init_node_get_all(context)

        active_monitor_list = []
        for monitor_node in server_list:
            #LOG.info("monitor_node:%s" % monitor_node)
            if monitor_node['status'] == "Active" \
               and monitor_node['type'].find('monitor') != -1:
                if not __is_in(monitor_node['host']):
                    active_monitor_list.append(monitor_node)
        if len(active_monitor_list) < 1:
            LOG.error('There must be 1 monitor in the cluster')
            try:
                raise MonitorException
            except:
                LOG.error("There must be 1 monitor in the cluster")

        # select an active monitor
        idx = random.randint(0, len(active_monitor_list)-1)
        LOG.info("monitor_node:%s" % active_monitor_list[idx])
        return active_monitor_list[idx]

    def add_monitor(self, context, server_list):
        # monitor will be add
        new_monitor_list = [x for x in server_list if x['is_monitor']]
        LOG.info("new_monitor_list  %s" % new_monitor_list)
        if len(new_monitor_list) < 1:
            LOG.info("no monitor will be add")
            return True

        #active_monitor = self._get_active_monitor(context)
        #LOG.info("active_monitor:%s" % active_monitor)

        error_num = 0
        for ser in new_monitor_list:
            try:
                self._start_add(context, ser['id'])
                # get ceph_config
                ceph_config = self._get_ceph_config(context)

                # gen mon_id
                #LOG.info('add monitor get mon id----')
                #host_ip = db.init_node_get_by_host(context,host = ser['host'])['secondary_public_ip']
                #ip = host_ip.split(',')[0]
                # monitor_address = '%s:%s/0' % (ip, str(6789))
                # mon_ref = db.monitor_get_by_address(context, monitor_address,read_deleted = 'yes')
                # if mon_ref is not None:
                #     mon_id = mon_ref['name']
                # else:
                monitor_list = []
                for x in ceph_config:
                    if x.startswith("mon."):
                        try:
                            monitor_list.append(int(x.replace("mon.","")))
                        except:
                            pass
                monitor_list.sort()
                deleted_times = db.cluster_get_deleted_times(context,
                                                             ser['cluster_id'])
                if len(monitor_list) == 0:
                    monitor_list.append(0)
                mon_id = str(monitor_list.pop() + 1 + deleted_times)

                LOG.info("new_monitor id %s" % mon_id)

                # Update ceph.conf and keyring.admin from DB.
                LOG.info("add new monitor id save config")
                self._agent_rpcapi.update_ceph_conf(context, ser['host'])
                LOG.info("add new monitor id save keyring")
                self._agent_rpcapi.update_keyring_admin_from_db(context,
                                                                ser['host'])
                # add mon
                self._agent_rpcapi.add_monitor(context,
                                               host_id=ser['id'],
                                               mon_id=mon_id,
                                               host=ser['host'])

                self._add_success(context, ser['id'], "monitor")
            except rpc_exc.Timeout:
                error_num += 1
                self._conductor_api.init_node_update_status_by_id(context,
                    ser['id'], 'ERROR: add_monitor timeout error')
            except rpc_exc.RemoteError:
                error_num += 1
                self._conductor_api.init_node_update_status_by_id(context,
                    ser['id'], 'ERROR: add_monitor remote error')
            except:
                error_num += 1
                self._conductor_api.init_node_update_status_by_id(context,
                    ser['id'], 'ERROR: add_monitor')

        if error_num > 1:
            LOG.error('There are error occurs in add_monitor')
            raise

        return True

    def remove_monitors(self, context, server_list):
        # Check monitors list.
        # If not monitor to remove, return.
        remove_monitor_list = []
        for x in server_list:
            if x['type'].find('monitor') != -1:
                remove_monitor_list.append(x)
        LOG.info('removing monitor %s ' % remove_monitor_list)
        if len(remove_monitor_list) <= 0:
            return True

        # Select active monitors from db.
        server_list = db.init_node_get_all(context)
        active_monitor_list = []
        for monitor_node in server_list:
            if monitor_node['status'] == "Active" \
               and monitor_node['type'].find('monitor') != -1:
                active_monitor_list.append(monitor_node)
        if len(active_monitor_list) - len(remove_monitor_list) < 1:
            LOG.error('There must be 1 monitor in the cluster')
            try:
                raise MonitorRemoveFailed
            except Exception, e:
                LOG.error("%s: %s " %(e.code, e.message))
            return False

        # select an active monitor
        remove_mon_ids = [mon['id'] for mon in remove_monitor_list]
        LOG.info('remove mon ids %s' % remove_mon_ids)

        active_monitors = []
        for mon in active_monitor_list:
            if not mon['id'] in remove_mon_ids:
                active_monitors.append(mon)

        active_monitor = random.choice(active_monitors)
        mon_host = active_monitor['host']
        LOG.info('active monitor: %s' % mon_host)

        error_num = 0
        for ser in remove_monitor_list:
            try:
                # remove mon
                self._start_remove(context, ser['id'])
                self._agent_rpcapi.remove_monitor(context,
                        ser['id'], mon_host)
                time.sleep(60)
                self._agent_rpcapi.update_mon_state(context, active_monitor['host'])
                is_unavail = True if ser['status'] == 'unavailable' else False
                self._remove_success(context,
                                     ser['id'],
                                     "monitor",
                                     is_unavail=is_unavail)
            except rpc_exc.Timeout:
                error_num += 1
                self._conductor_api.init_node_update_status_by_id(context,
                    ser['id'], 'ERROR: remove_monitor rpc timeout error')
            except rpc_exc.RemoteError:
                error_num += 1
                self._conductor_api.init_node_update_status_by_id(context,
                    ser['id'], 'ERROR: remove_monitor rpc remote error')
            except:
                error_num += 1
                self._conductor_api.init_node_update_status_by_id(context,
                    ser['id'], 'ERROR: remove_monitor')
        if error_num > 1:
            LOG.error('there are some error occured in remove_monitor')
            raise
        return True

    def _get_active_node(self, context, beyond_list):
        def __is_in(host):
            if not beyond_list:
                return False
            for ser in beyond_list:
                if ser['host'] == host:
                    return True
            return False

        server_list = db.init_node_get_all(context)

        active_monitor_list = []
        for monitor_node in server_list:
            #LOG.info("monitor_node:%s" % monitor_node)
            if monitor_node['status'] == "Active":
                if not __is_in(monitor_node['host']):
                    active_monitor_list.append(monitor_node)

        # select an active monitor
        idx = random.randint(0, len(active_monitor_list)-1)
        LOG.info("monitor_node:%s" % active_monitor_list[idx])
        return active_monitor_list[idx]

    def add_mds(self, context, server_list):
        try:
            active_monitor = self._get_active_node(context, server_list)
            self._agent_rpcapi.add_mds(context, host=active_monitor['host'])
        except rpc_exc.Timeout:
            self._update_server_list_status(context,
                server_list, 'rpc timeout error: check network')
        except rpc_exc.RemoteError:
            self._update_server_list_status(context,
                server_list, 'rpc remote error')
        except:
            self._update_server_list_status(context,
                server_list, 'ERROR: add_mds')

    def add_osd(self, context, server_list):
        # storage will be add
        new_storage_list = [x for x in server_list if x['is_storage']]
        LOG.info("new_storage_list  %s" % new_storage_list)

        # select an active monitor
        #active_monitor = self._get_active_monitor(context)
        active_monitor = None
        for ser in new_storage_list:
            try:
                self._start_add(context, ser['id'])
                # update zone_id
                values = {"zone_id": ser['zone_id']}
                self._conductor_rpcapi.init_node_update(context,
                                                        ser['id'],
                                                        values)
                # save ceph conf
                #LOG.info(" save osd_location of osd in  %s " % ser['osd_locations'])
                for osd_location in ser.get('osd_locations',[]):
                    values = {'osd_location':osd_location.get('location',None),
                              'weight':osd_location.get('weight'),}
                    osd_id = int(osd_location['id'])

                    db.osd_state_update(context,osd_id,values)
                LOG.info(" start save ceph config to %s " % ser['host'])
                self._agent_rpcapi.update_ceph_conf(context, ser['host'])
                # save admin keyring
                LOG.info(" start save ceph keyring to %s " % ser['host'])
                self._update_server_list_status(context,[ser],'update keyring')
                self._agent_rpcapi.update_keyring_admin_from_db(context,
                                                                ser['host'])

                LOG.info('Begin to add osd in agent host = %s' % ser['host'])
                self._update_server_list_status(context, [ser], 'add osds')
                self._agent_rpcapi.add_osd(context,
                                           ser['id'],
                                           ser['host'])

                #update osd status, capacity, weight
                cluster_id = ser['cluster_id']
                active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
                self._agent_rpcapi.update_osd_state(context, active_monitor['host'])

                LOG.info("add storage success")
                self._add_success(context, ser['id'], "storage")
            except rpc_exc.Timeout:
                self._update_server_list_status(context,
                                                new_storage_list,
                                                'ERROR: add_osd rpc timeout')
            except rpc_exc.RemoteError:
                self._update_server_list_status(context,
                                                new_storage_list,
                                                'ERROR: add_osd rpc remote error')
            except:
                self._update_server_list_status(context,
                                                new_storage_list,
                                                'ERROR: add_osd error')
                raise
        if active_monitor is not None:
            self._agent_rpcapi.update_zones_from_crushmap_to_db(context,None,
                active_monitor['host'])
        return True

    def remove_osd(self, context, server_list):
        remove_storage_list = [x for x in server_list if x['remove_storage']]
        LOG.info('removing storages %s ' % remove_storage_list)

        #active_monitor = self._get_active_monitor(context)
        #LOG.info('active_monitor = %s' % active_monitor['host'])

        for ser in remove_storage_list:
            try:
                self._start_remove(context, ser['id'])
                # remove storage
                cluster_id = ser['cluster_id']
                active_monitor = self._get_active_monitor(context,cluster_id=cluster_id)
                self._agent_rpcapi.remove_osd(context,
                                              ser['id'],
                                              active_monitor['host'])
                self._agent_rpcapi.update_osd_state(context,
                                                    active_monitor['host'])
                is_unavail = True if ser['status'] == 'unavailable' else False
                self._remove_success(context,
                                     ser['id'],
                                     "storage",
                                     is_unavail=is_unavail)
            except rpc_exc.Timeout:
                self._update_server_list_status(context, server_list,
                    'ERROR: remove_osd rpc timeout error')
            except rpc_exc.RemoteError:
                self._update_server_list_status(context, server_list,
                    'ERROR: remove_osd rpc remote error')
            except:
                self._update_server_list_status(context, server_list,
                    'ERROR')
                raise
        return True

    def remove_mds(self, context, server_list):
        remove_storage_list = [x for x in server_list if x['mds'] == 'yes']
        LOG.info('removing mds %s ' % remove_storage_list)

        #active_monitor = self._get_active_monitor(context)
        #LOG.info('active_monitor = %s' % active_monitor['host'])
        try:
            for ser in remove_storage_list:
                self._start_remove(context, ser['id'])
                # remove storage
                cluster_id = ser['cluster_id']
                active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
                self._agent_rpcapi.remove_mds(context,
                                              ser['id'],
                                              active_monitor['host'])
                is_unavail = True if ser['status'] == 'unavailable' else False
                self._remove_success(context,
                                     ser['id'],
                                     "mds",
                                     is_unavail=is_unavail)
        except rpc_exc.Timeout:
            for ser in remove_storage_list:
                self._conductor_api.init_node_update_status_by_id(context,
                    ser['id'], 'ERROR: remove_mds rpc timeout error')
        except rpc_exc.RemoteError:
            for ser in remove_storage_list:
                self._conductor_api.init_node_update_status_by_id(context,
                    ser['id'], 'ERROR: remove_mds rpc remote error')
        except:
            for ser in remove_storage_list:
                self._conductor_api.init_node_update_status_by_id(context,
                    ser['id'], 'ERROR: remove_mds')
        return True

    def _update_init_node(self, context, server_list):
        def __update_db(ser):
            values = {}
            values['id'] = ser['id']
            node_type = ""
            if ser['is_storage'] == True:
                node_type += "storage,"
            if ser['is_monitor'] == True:
                node_type += "monitor,"
            if ser['is_rgw'] == True:
                node_type += "rgw,"
            values['type'] = node_type
            db.init_node_update(context, ser['id'], values)

        thd_list = []
        for ser in server_list:
            thd = utils.MultiThread(__update_db, ser=ser)
            thd_list.append(thd)
        utils.start_threads(thd_list)

    def _compute_pg_num(self, context, host, osd_num, replication_num):
        """compute pg_num"""
        try:
            pg_count_factor = 100
            settings = db.vsm_settings_get_all(context)
            for setting in settings:
                if setting['name'] == 'pg_count_factor':
                    pg_count_factor = int(setting['value'])

            pg_num = pg_count_factor * osd_num//replication_num

        except ZeroDivisionError,e:
            raise ZeroDivisionError
        if pg_num < 1:
            msg = _("Could not compute proper pg_num.")
            raise
        return pg_num

    def _judge_drive_ext_threshold(self, context):
        storage_groups = db.storage_group_get_all(context);
        active_monitor = self._get_active_monitor(context)
        update_pool_state_tag = False;
        for storage_group in storage_groups:
            osd_num = db.osd_state_count_by_storage_group_id(context, storage_group['id'])
            update_db_tag = False;
            if osd_num >= 2 * storage_group['drive_extended_threshold']:
                pools = db.pool_get_by_ruleset(context, storage_group['rule_id'])
                for pool in pools:
                    pg_num = self._compute_pg_num(context, active_monitor['host'],\
                                                    osd_num, pool['size'])
                    osds_total_num = self._agent_rpcapi.get_osds_total_num(context,\
                                                active_monitor['host'])
                    LOG.info("There are %s osds in ceph." % osds_total_num)
                    step_max_pg_num = osds_total_num * 32
                    max_pg_num = step_max_pg_num + pool.get('pg_num')
                    if pg_num > max_pg_num:
                        pg_num = max_pg_num
                        update_pool_state_tag = True
                        update_db_tag = True;
                        self._agent_rpcapi.set_pool_pg_pgp_num(context, \
                                           active_monitor['host'], \
                                           pool['name'], pg_num, pg_num)

                    elif pg_num > pool.get('pg_num'):
                        update_pool_state_tag = True
                        update_db_tag = True;
                        self._agent_rpcapi.set_pool_pg_pgp_num(context, \
                                           active_monitor['host'], \
                                           pool['name'], pg_num, pg_num)

                if update_db_tag:
                    #update db
                    values = {
                                'drive_extended_threshold': osd_num,
                             }
                    db.storage_group_update(context, storage_group['id'], values)
                    LOG.info("update storage_group drive extended threshold")
        if update_pool_state_tag:
            #update pool status
            LOG.info("update_pool_state")
            self._agent_rpcapi.update_pool_state(context, active_monitor['host'])

    def _update_drive_ext_threshold(self, context):
        storage_groups = db.storage_group_get_all(context);
        for storage_group in storage_groups:
            drive_num = db.osd_state_count_by_storage_group_id(context, storage_group['id'])
            values = {
                        'drive_extended_threshold': drive_num,
                     }
            db.storage_group_update(context, storage_group['id'], values)

    @utils.single_lock
    def add_servers(self, context, body=None):
        """Add the servers into ceph cluster.

           It's notable that, the type of body['servers']
           looks as below:

                [
                    {u'is_storage': True,
                     u'is_monitor': True,
                     u'id': u'1',
                     u'zone_id': u'1',
                     u'osds_locations':[{'osd_id':1,'location':zone_id},{'osd_id':2,'location':zone_id2}]},
                    {u'is_storage': True,
                     u'is_monitor': False,
                     u'id': u'2',
                     u'zone_id': u'2',
                     u'osds_locations':[{'osd_id':1,'location':zone_id},{'osd_id':2,'location':zone_id2}]},
                ]

           Here we also need to fetch info from DB.
        """
        def _update_ssh_key():
            server_list = db.init_node_get_all(context)
            for ser in server_list:
                if ser['status'] == 'Active' or ser['status'] == 'available':
                    self._agent_rpcapi.update_ssh_keys(context, ser['host'])

        server_list = body['servers']
        for ser in server_list:
            ser_ref = db.init_node_get(context, int(ser['id']))
            ser['host'] = ser_ref['host']
            ser['cluster_id'] = self._agent_rpcapi.cluster_id(context,
                                                              ser['host'])
            # It need to change the role defined in
            # server.manifest
            if ser['is_monitor'] == False:
                if ser['is_storage'] == True and ser_ref['status'] == 'available':
                    values = {'type': 'storage'}
                    db.init_node_update(context, ser_ref['id'], values)
            if ser['is_monitor'] == True:
                if ser_ref['type'].find('monitor') != -1 and ser_ref['status'] == 'Active':
                    ser['is_monitor'] = False
                if ser['is_storage'] == False and ser_ref['status'] == 'available':
                    values = {'type': 'monitor'}
                    db.init_node_update(context, ser_ref['id'], values)
                elif ser['is_storage'] == True and ser_ref['status'] == 'available':
                    values = {'type': 'storage,monitor'}
                    db.init_node_update(context, ser_ref['id'], values)
                

        self._update_server_list_status(context, server_list, 'update ssh key')
        _update_ssh_key()
        self._update_server_list_status(context, server_list, 'add monitor')
        self.add_monitor(context, server_list)

        # Begin to add osds.
        LOG.info("start to add storage")
        self.add_osd(context, server_list)

        #self._judge_drive_ext_threshold(context)
        return True

    @utils.single_lock
    def remove_servers(self, context, body=None):
        """
                [
                    {u'remove_storage': True,
                     u'remove_monitor': True,
                     u'id': u'1',
                     u'zone_id': u'1'},
                    {u'remove_storage': True,
                     u'remove_monitor': False,
                     u'id': u'2',
                     u'zone_id': u'2'}
                ]

        """
        server_list = body['servers']
        LOG.info('remove_servers = %s ' % server_list)
        if len(server_list) <= 0:
            return True

        need_change_mds = False
        for ser in server_list:
            ser_ref = db.init_node_get(context, ser['id'])
            ser['host'] = ser_ref['host']
            ser['type'] = ser_ref['type']
            ser['remove_monitor'] = ser['type'].find('monitor') != -1
            ser['status'] = ser_ref['status']
            ser['mds'] = ser_ref['mds']
            ser['service_id'] = ser_ref['service_id']
            if ser['mds'] == 'yes':
                need_change_mds = True

        try:
            LOG.info("start to remove monitor")
            self.remove_monitors(context, server_list)

            LOG.info("start to remove storage")
            self.remove_osd(context, server_list)
            values = {'osd_name': "osd.%s"%FLAGS.vsm_status_uninitialized,
                      'osd_location':'',
                      'deleted':0,
                      'state':FLAGS.vsm_status_uninitialized,}
            LOG.info("update deleted osd to uninited")
            for server in server_list:
                service_id = server['service_id']
                db.update_deleted_osd_state_by_service_id(context,service_id,values)
            LOG.info("update deleted osd to uninited over")


            if need_change_mds:
                LOG.info("start to remove mds")
                self.remove_mds(context, server_list)
                # self.add_mds(context, server_list)
            return True
        except rpc_exc.Timeout:
            self._update_server_list_status(context,
                                            server_list,
                                            'rpc timeout error: check network')
        except rpc_exc.RemoteError:
            self._update_server_list_status(context,
                                            server_list,
                                            'rpc remote error: check network')
        except:
            self._update_server_list_status(context,
                                            server_list,
                                            'ERROR')
            raise

    @utils.single_lock
    def stop_cluster(self, context, body=None):
        """Noout and stop all osd service, then stop the server.
           body = {u'servers': [{u'cluster_id': 1, u'id': u'1'},
                        {u'cluster_id': 1, u'id': u'2'}]}
        """
        LOG.info("DEBUG in stop cluster in scheduler manager.")

        server_list = body['servers']
        active_monitor = server_list[0]
        self._update_server_list_status(context,
                                            server_list,
                                            'stopping')
        try:
            self._agent_rpcapi.stop_cluster(context, active_monitor['host'])
            self._update_server_list_status(context,
                                    server_list,
                                    'stopped')
        except rpc_exc.Timeout:
            self._update_server_list_status(context,
                                            server_list,
                                            'rpc timeout error: check network')
        except rpc_exc.RemoteError:
            self._update_server_list_status(context,
                                            server_list,
                                            'rpc remote error: check network')
        except:
            self._update_server_list_status(context,
                                            server_list,
                                            'ERROR')
            raise

        return True

    @utils.single_lock
    def start_cluster(self, context, body=None):
        """Start all osd service, then start the server.
           body = {u'servers': [{u'cluster_id': 1, u'id': u'1'},
                        {u'cluster_id': 1, u'id': u'2'}]}
        """
        LOG.info("DEBUG in start cluster in scheduler manager.")
        server_list = body['servers']
        active_monitor = server_list[0]
        self._update_server_list_status(context,
                                    server_list,
                                    'starting')
        try:
            self._agent_rpcapi.start_cluster(context, active_monitor['host'])
            self._update_server_list_status(context,
                                    server_list,
                                    'Active')
        except rpc_exc.Timeout:
            self._update_server_list_status(context,
                                            server_list,
                                            'rpc timeout error: check network')
        except rpc_exc.RemoteError:
            self._update_server_list_status(context,
                                            server_list,
                                            'rpc remote error: check network')
        except:
            self._update_server_list_status(context,
                                            server_list,
                                            'ERROR')
            raise

        return True

    @utils.single_lock
    def stop_server(self, context, body=None):
        """Noout and stop all osd service, then stop the server.
           body = {u'servers': [{u'cluster_id': 1, u'id': u'1'},
                        {u'cluster_id': 1, u'id': u'2'}]}
        """
        LOG.info("DEBUG in stop server in scheduler manager.")

        server_list = body['servers']
        need_change_mds = False
        for ser in server_list:
            ser_ref = db.init_node_get(context, ser['id'])
            ser['host'] = ser_ref['host']
            if ser_ref['mds'] == 'yes':
                need_change_mds = True

        #active_monitor = self._get_active_monitor(context)
        LOG.info("stop_server of scheduer manager %s" % server_list)
        for item in server_list:
            res = db.init_node_get(context, item['id'])
            self._start_stop(context, item['id'])
            try:
                self._agent_rpcapi.stop_server(context,
                                               item['id'],
                                               res['host'])
                try:
                    cluster_id = res['cluster_id']
                    active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
                    self._agent_rpcapi.update_osd_state(context, active_monitor['host'])
                except:
                    pass

            except rpc_exc.Timeout:
                self._update_server_list_status(context,
                                                server_list,
                                                'rpc timeout error: check network')
            except rpc_exc.RemoteError:
                self._update_server_list_status(context,
                                                server_list,
                                                'rpc remote error: check network')
            except:
                self._update_server_list_status(context,
                                                server_list,
                                                'ERROR')
                raise

        # active_count = db.init_node_count_by_status(context,status='Active')
        # if need_change_mds and active_count > 0:
        #     self.add_mds(context, server_list)
        return True


    @utils.single_lock
    def ceph_upgrade(self, context, body=None):
        """upgrade ceph.
           body = {u'servers': [{u'cluster_id': 1, u'id': u'1','host':''},
                        {u'cluster_id': 1, u'id': u'2','host':''}],
                        'key_url':"https://...",
                        'proxy':"https://...",
                        'ssh_user':"root",
                        'pkg_url':"https://..."}
        """
        LOG.info("DEBUG in ceph upgrade in scheduler manager.")
        server_list = body.get('servers')
        if not server_list:
            server_list = db.init_node_get_all(context)
        pre_ceph_ver = server_list[0]['ceph_ver']
        hosts = [server['host'] for server in server_list]
        hosts = ','.join(hosts)
        key_url = body['key_url']
        pkg_url = body['pkg_url']
        proxy = body['proxy']
        ssh_user = body.get('ssh_user','')
        #check network and get pakages from network
        LOG.info('scheduler/manager.py ceph_upgrade==%s'%body)
        LOG.info("ceph upgrade of scheduer manager %s" % server_list)
        status_all = [node['status'] for node in server_list ]
        status_all = list(set(status_all))
        message = "send commonds success"
        if len(status_all)==1 and status_all[0] in ['available','Active']:
            err = 'success'
            try:
                out, err = utils.execute('vsm-ceph-upgrade','-k',
                                 key_url,'-p', pkg_url,'-s',hosts,'--proxy',proxy,'--ssh_user',ssh_user,
                                 run_as_root=True)
                LOG.info("exec vsm-ceph-upgrade in controller node:%s--%s"%(out,err))
                err = 'success'
            except:
                LOG.info("vsm-ceph-upgrade in controller node:%s"%err)
                return {"message":"ceph upgrade unsuccessful.Please make sure that the URLs are reachable."}

            if status_all[0] == 'available':
                restart = False
            else:
                restart = True
            def __ceph_upgrade(context, node_id, host, key_url, pkg_url,restart):
                self._agent_rpcapi.ceph_upgrade(context, node_id, host, key_url, pkg_url,restart)

            thd_list=[]
            self._update_server_list_status(context,
                                                    server_list,
                                                    'ceph upgrading')
            for item in server_list:
                thd = utils.MultiThread(__ceph_upgrade,context=context, node_id=item['id'], host=item['host'], key_url=key_url,pkg_url=pkg_url,restart=restart)
                thd_list.append(thd)
            utils.start_threads(thd_list)
        else:
            return {"message":"ceph upgrade unsuccessful.Please add all available servers to ceph cluster firstly."}
        server_list_new = db.init_node_get_all(context)
        new_ceph_ver = server_list_new[0]['ceph_ver']
        if new_ceph_ver != pre_ceph_ver:
            message = "ceph upgrade from %s to %s success"%(pre_ceph_ver,new_ceph_ver)
        else:
            message = "ceph upgrade unsuccessful.Please make sure that the URLs are reachable."
        return {"message":message}

    @utils.single_lock
    def start_server(self, context, body=None):
        """Start all osd service, then start the server.
           body = {u'servers': [{u'cluster_id': 1, u'id': u'1'},
                        {u'cluster_id': 1, u'id': u'2'}]}
        """
        LOG.info("DEBUG in start server in scheduler manager.")
        server_list = body['servers']
        #active_monitor = self._get_active_monitor(context)
        for item in server_list:
            res = db.init_node_get(context, item['id'])
            self._start_start(context, item['id'])
            try:
                self._agent_rpcapi.start_server(context, item['id'], res['host'])
                try:
                    cluster_id = res['cluster_id']
                    active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
                    self._agent_rpcapi.update_osd_state(context, active_monitor['host'])
                except:
                    pass
            except rpc_exc.Timeout:
                self._update_server_list_status(context,
                                                server_list,
                                                'rpc timeout error: check network')
            except rpc_exc.RemoteError:
                self._update_server_list_status(context,
                                                server_list,
                                                'rpc remote error: check network')
            except:
                self._update_server_list_status(context,
                                                server_list,
                                                'ERROR')
                raise

        return True

    def get_cluster_list(self, context):
        res = self._conductor_rpcapi.get_server_list(context)
        LOG.info('scheduler/manager.py get cluster_list values %s' % res)
        return res

    def get_ceph_health_list(self, context, body=None):
        cluster_id = body and body.get('cluster_id',1) or 1
        active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
        res = self._agent_rpcapi.get_ceph_health_list(context,active_monitor['host'])
        LOG.info('scheduler/manager.py get_ceph_health_list values %s' % res)
        return res

    def _get_monitor_by_cluster_id(self, context, cluster_id):
        node_ref = self._conductor_rpcapi.init_node_get_by_cluster_id(context,
                                                            cluster_id)
        if node_ref is None:
            return False

        hosts_list = []
        LOG.info("DEBUG return %s" % str(node_ref))
        for node in node_ref:
            LOG.info("DEBUG node from conductor %s" % str(node))
            LOG.info("DEBUG type is %s" % node['type'])
            if node['type'].find('monitor') != -1:
                hosts_list.append(node['host'])

        num = len(hosts_list)
        if num == 0:
            return False

        idx = random.randint(0, num-1)
        LOG.info("DEBUG randomly select the host %s" % hosts_list[idx])
        return hosts_list[idx]

    @utils.single_lock
    def add_new_zone(self, context, values):
        """Add a new zone to the database and crushmap
          values = {u'zone':
                        {u'cluster_id': 1,
                         u'name': u'test-zone'
                        }
                   }
        """
        LOG.info("DEBUG in add_new_zone in scheduler %s", values)
        host = self._get_monitor_by_cluster_id(context, values['zone']['cluster_id'])
        if host == False:
            LOG.error("No available monitor node returns!")
            return False

        res = self._agent_rpcapi.add_new_zone(context, values['zone']['name'], host)
        return True

    def _track_monitors(self, context, server_list):
        """Checking if all the monitors are in the quorum."""
        def _track_single_monitor(context, server):
            """Tracking single monitor."""
            service_id = server['id']
            def _update(status):
                values = {'status': status}
                self._conductor_rpcapi.init_node_update(context,
                                                    service_id,
                                                    values)
                if status.lower().find('error') != -1:
                    raise
            try:
                _update('Checking monitor')
                jsout = self._agent_rpcapi.track_monitors(context,
                                                          server['host'])
                try_times = 0
                while try_times < 60 and \
                      len(jsout['quorum']) < len(server_list):
                    jsout = self._agent_rpcapi.track_monitors(context,
                                                              server['host'])
                    time.sleep(3)
                    try_times = try_times + 1

                _update('Success: checking monitor')
            except:
                _update('ERROR: checking monitor status')

        thread_list = []
        for ser in server_list:
            if ser['is_monitor']:
                thd = utils.MultiThread(_track_single_monitor,
                                         context=context,
                                         server=ser)
                thread_list.append(thd)
        utils.start_threads(thread_list)

    @utils.single_lock
    def import_ceph_conf(self, context, cluster_id, ceph_conf_path):
        """
        """
        LOG.info('import ceph conf from %s to db '%ceph_conf_path)#ceph_conf_path!=FLAG.ceph_conf
        ceph_conf_parser = cephconfigparser.CephConfigParser(str(ceph_conf_path))._parser
        ceph_conf_str = ceph_conf_parser.as_str()
        db.cluster_update_ceph_conf(context, cluster_id, ceph_conf_str)
        server_list = db.init_node_get_all(context)
        LOG.info('import ceph conf from db to ceph nodes ')
        for ser in server_list:
            LOG.info('import ceph conf from db to ceph nodes %s '%ser['host'])
            self._agent_rpcapi.update_ceph_conf(context, ser['host'])
        LOG.info('import ceph conf from db to ceph nodes success ')
        return {"message":"success"}

    def integrate_cluster(self, context, server_list):
        """ integrate an exsiting cluster previosuly created by VSM
        :param context:
        :param server_list:
        :return:
        """

        LOG.info('integrate cluster by syncing OSDs and refreshing status')
        server_list = db.init_node_get_all(context)
        for srv in server_list:
            self._agent_rpcapi.integrate_cluster_sync_osd_states(context, srv['host'])
        active_server = self._set_active_server(context)
        #TODO db.update_mount_points()
        return self._agent_rpcapi.integrate_cluster_update_status(context, active_server['host'])
    #
    # def check_pre_existing_cluster(self,context,body):
    #     '''
    #     :param context:
    #     :param body:
    #     {u'cluster_conf': u'/etc/ceph/ceph.conf', u'monitor_host_name': u'centos-storage1', u'monitor_host_id': u'1', u'monitor_keyring': u'/etc/keying'}
    #     :return:
    #     '''
    #     monitor_pitched_host = body.get('monitor_host_name')
    #     message = {}
    #     try:
    #         message = self._agent_rpcapi.check_pre_existing_cluster(context, body, monitor_pitched_host)
    #     except rpc_exc.Timeout:
    #         LOG.error('ERROR: check_pre_existing_cluster rpc timeout')
    #     except rpc_exc.RemoteError:
    #         LOG.error('ERROR: check_pre_existing_cluster rpc remote')
    #     except:
    #         LOG.error('ERROR: check_pre_existing_cluster')
    #         raise
    #     return message

    def check_pre_existing_cluster(self, context, body):
        messages = []
        message_ret = {'code':[],'error':[],'info':[]}
        #messages.append(self.check_network(context, body))
        message_cephconf = self.check_pre_existing_ceph_conf(context, body)
        messages.append(message_cephconf)
        message_crushmap = self.check_pre_existing_crushmap(context, body)
        crushmap_tree_data = message_crushmap['tree_data']
        messages.append(message_crushmap)
        if message_cephconf['osd_num'] != message_crushmap['osd_num']:
            message_ret['code'].append('-1')
            message_ret['error'].append('osd quantity is not consistent between ceph conf and crush map.')
        for message in messages:
            message_ret['code'] = message_ret['code']+message['code']
            message_ret['error'] = message_ret['error']+message['error']
            message_ret['info'] = message_ret['info']+message['info']
        for key,value in message_ret.iteritems():
            message_ret[key] = ','.join(value)
        message_ret['crushmap_tree_data'] = crushmap_tree_data
        return message_ret



    def check_pre_existing_ceph_conf(self, context, body):
        message = {'code':[],'error':[],'info':[]}
        ceph_conf = body.get('ceph_conf')
        ceph_conf_file_new = '%s-check'%FLAGS.ceph_conf
        utils.write_file_as_root(ceph_conf_file_new, ceph_conf, 'w')
        config = cephconfigparser.CephConfigParser(fp=ceph_conf_file_new)
        config_dict = config.as_dict()
        if config_dict is None:
            message['code'].append('-26')
            message['error'].append('the format of ceph_conf error.')
        osd_list = []
        osd_header = {}
        mon_list = []
        mds_list = []
        mds_header = {}
        mon_header = {}
        global_header = {}
        for key,value in config_dict.iteritems():
            if key:
                if key.find('osd.')!=-1:
                    osd_list.append({key:value})
                elif key.find('osd')!=-1:
                    osd_header = value
                elif key.find('mon.')!=-1:
                    mon_list.append({key:value})
                elif key.find('mon')!=-1:
                    mon_header = value
                elif key.find('mds.')!=-1:
                    mds_list.append({key:value})
                elif key.find('mds')!=-1:
                    mds_header = value
                elif key.find('global')!=-1:
                    global_header = value
        # if not global_header:
        #     message['code'].append('-21')
        #     message['error'].append('missing global section in ceph configration file.')
        # else:
        #     pass
        # if not mon_header:
        #     message['code'].append('-22')
        #     message['error'].append('missing mon header section in ceph configration file.')
        # else:
        #     pass
        # if not osd_header:
        #     message['code'].append('-23')
        #     message['error'].append('missing osd header section in ceph configration file.')
        # else:
        #     pass

        osd_fields = ['devs','host','cluster addr','public addr','osd journal']
        for osd in osd_list:
            osd_name = osd.keys()[0]
            fields_missing = set(osd_fields) - set(osd[osd_name].keys())
            if len(fields_missing) > 0:
                message['code'].append('-24')
                message['error'].append('missing field %s for %s in ceph configration file.'%(fields_missing,osd_name))

        mon_fields = ['host','mon addr']
        for mon in mon_list:
            mon_name = mon.keys()[0]
            fields_missing = set(mon_fields) - set(mon[mon_name].keys())
            if len(fields_missing) > 0:
                message['code'].append('-25')
                message['error'].append('missing field %s for %s in ceph configration file.'%(fields_missing,mon_name))
        message['osd_num'] = len(osd_list)
        return message


    def check_pre_existing_crushmap(self, context, body):
        '''

        :param context:
        :param body:
        {u'ceph_conf': u'****', u'crush_map': u'****'}
        :return:
        '''

        code = []
        error = []
        info = []
        crushmap_str = body.get('crush_map')
        crush_map_new = '%s-crushmap.json'%FLAGS.ceph_conf
        utils.write_file_as_root(crush_map_new, crushmap_str, 'w')
        osd_num = 0
        tree_node = None
        try:
            crushmap = CrushMap(json_file=crush_map_new)
            tree_node = crushmap._show_as_tree_dict()
            osd_num = len(crushmap._devices)
            rule_check = []
            for rule in crushmap._rules:
                rule_check_ret = crushmap.get_storage_groups_by_rule(rule)
                if type(rule_check) == str:
                  rule_check.append(rule_check_ret)

            if type(tree_node) == str:
                error.append(tree_node)
                code.append('-11')
            if rule_check:
                error = error + rule_check
                code.append('-12')
        except:
            error.append('crusmap format error.')
            code.append('-13')

        message = {'code':code,'error':error,'info':info,'osd_num':osd_num,'tree_data':tree_node}
        return message

    def detect_cephconf(self,context,body):
        '''
        :param context:
        :param body:
        { u'monitor_host_name': u'centos-storage1', u'monitor_id': u'1', u'monitor_keyring': u'******'}
        :return:
        '''
        monitor_pitched_host = body.get('monitor_host_name')
        monitor_keyring = body.get('monitor_keyring')
        message = {}
        try:
            message = self._agent_rpcapi.detect_cephconf(context, monitor_keyring, monitor_pitched_host)
        except rpc_exc.Timeout:
            LOG.error('ERROR: detect_cephconf rpc timeout')
        except rpc_exc.RemoteError:
            LOG.error('ERROR: detect_cephconf rpc remote')
        except:
            LOG.error('ERROR: detect_cephconf')
            raise
        return message

    def detect_crushmap(self,context,body):
        '''
        :param context:
        :param body:
        { u'monitor_host_name': u'centos-storage1', u'monitor_id': u'1', u'monitor_keyring': u'******'}
        :return:
        '''
        monitor_pitched_host = body.get('monitor_host_name')
        monitor_keyring = body.get('monitor_keyring')
        message = {}
        try:
            message = self._agent_rpcapi.detect_crushmap(context, monitor_keyring, monitor_pitched_host)
        except rpc_exc.Timeout:
            LOG.error('ERROR: check_pre_existing_cluster rpc timeout')
        except rpc_exc.RemoteError:
            LOG.error('ERROR: check_pre_existing_cluster rpc remote')
        except:
            LOG.error('ERROR: check_pre_existing_cluster')
            raise
        return message

    def get_crushmap_tree_data(self,context,body):
        '''
        :param context:
        :param body:
        { u'cluster_id":1}
        :return:
        '''
        monitor_pitched_host = self._get_monitor_by_cluster_id(context, body.get('cluster_id',1))
        #LOG.info("000000000000000=%s"%monitor_pitched_host)
        monitor_keyring = None
        tree_node = []
        try:
            #LOG.info("111111111111111=%s"%monitor_pitched_host)
            message = self._agent_rpcapi.detect_crushmap(context, monitor_keyring, monitor_pitched_host)
            crushmap_str = message['crushmap']
            crush_map_new = '%s-crushmap.json'%FLAGS.ceph_conf
            utils.write_file_as_root(crush_map_new, crushmap_str, 'w')
            crushmap = CrushMap(json_file=crush_map_new)
            tree_node = crushmap._show_as_tree_dict()
            #LOG.info("222222==%s"%tree_node)
        except rpc_exc.Timeout:
            LOG.error('ERROR: get_crushmap_tree_data rpc timeout')
        except rpc_exc.RemoteError:
            LOG.error('ERROR: get_crushmap_tree_data rpc remote')
        except:
            LOG.error('ERROR: get_crushmap_tree_data')
            raise
        return {'tree_node':tree_node}

    def get_osds_by_rules(self,context,body):
        '''
        :param context:
        :param body:
        {'rules':[rule_name,rule_name],
         'cluster_id':1,
        }
        :return:
        '''
        monitor_pitched_host = self._get_monitor_by_cluster_id(context, body.get('cluster_id',1))
        #LOG.info("000000000000000=%s"%monitor_pitched_host)
        monitor_keyring = None
        rules = body.get('rules')
        rule_osds = {}
        try:
            #LOG.info("111111111111111=%s"%monitor_pitched_host)
            message = self._agent_rpcapi.detect_crushmap(context, monitor_keyring, monitor_pitched_host)
            crushmap_str = message['crushmap']
            crush_map_new = '%s-crushmap.json'%FLAGS.ceph_conf
            utils.write_file_as_root(crush_map_new, crushmap_str, 'w')
            crushmap = CrushMap(json_file=crush_map_new)
            for rule in rules:
                osds = crushmap.get_all_osds_by_rule(rule)
                osds = [osd['name'] for osd in osds]
                osds = list(set(osds))
                rule_osds[rule] = osds
            #LOG.info("222222==%s"%tree_node)
        except rpc_exc.Timeout:
            LOG.error('ERROR: get_crushmap_tree_data rpc timeout')
        except rpc_exc.RemoteError:
            LOG.error('ERROR: get_crushmap_tree_data rpc remote')
        except:
            LOG.error('ERROR: get_crushmap_tree_data')
            raise
        return rule_osds

    def import_cluster(self,context,body):
        '''
        :param context:
        :param body:
        {u'ceph_conf': u'****', u'monitor_host_name': u'centos-storage1', u'monitor_id': u'1', u'monitor_keyring': u'******'}
        :return:
        '''
        monitor_pitched_host = body.get('monitor_host_name')
        message = {}
        try:
            message = self._agent_rpcapi.check_pre_existing_cluster(context, body, monitor_pitched_host)
            LOG.info('check----result----%s'%message)
            if message.get('error'):
                return message
            else:
                message = self._agent_rpcapi.import_cluster(context, body, monitor_pitched_host)
            server_list = db.init_node_get_all(context)
            for ser in server_list:
                LOG.info('fresh ceph conf from db to ceph nodes %s '%ser['host'])
                self._agent_rpcapi.update_ceph_conf(context, ser['host'])
                self._agent_rpcapi.update_keyring_admin_from_db(context,ser['host'])
            LOG.info('fresh cluster status. monitor name is %s'%monitor_pitched_host)
            self._agent_rpcapi.cluster_refresh(context,monitor_pitched_host)
        except rpc_exc.Timeout:
            LOG.error('ERROR: check_pre_existing_cluster rpc timeout')
        except rpc_exc.RemoteError:
            LOG.error('ERROR: check_pre_existing_cluster rpc remote')
        except:
            LOG.error('ERROR: check_pre_existing_cluster')
            raise
        return message

    @utils.single_lock
    def create_cluster(self, context, server_list):
        """Add the servers into ceph cluster.

        It's notable that, the type of body['servers']
        looks as below:

           [
               {u'is_storage': True,
                u'is_monitor': True,
                u'is_mds': True,
                u'is_rgw': True,
                u'id': u'1',
                u'zone_id': u'1'},
               {u'is_storage': True,
                u'is_monitor': False,
                u'is_mds': False,
                u'is_rgw': False,
                u'id': u'2',
                u'zone_id': u'2'}
           ]

        Here we also need to fetch info from DB.
        """
        # Add hostname here.
        for ser in server_list:
            ser_ref = db.init_node_get(context, ser['id'])
            ser['host'] = ser_ref['host']


        def _update(status):
            LOG.debug('status = %s' % status)
            self._update_server_list_status(context,
                                            server_list,
                                            status)
            if status.lower().find('error') != -1:
                raise

        # Set at least 3 mons when creating cluster
        pool_default_size = db.vsm_settings_get_by_name(context,'osd_pool_default_size')
        pool_default_size = int(pool_default_size.value)
        nums = len(server_list)
        mds_node = None
        rgw_node = None
        if nums >= pool_default_size:
            count = 0
            rest_mon_num = 0
            for ser in server_list:
                if ser['is_monitor'] == True:
                    count += 1
                if ser['is_mds'] == True:
                    mds_node = ser
                if ser['is_rgw'] == True:
                    rgw_node = ser
            if count < pool_default_size:
                rest_mon_num = pool_default_size - count
            if rest_mon_num > 0:
                for ser in server_list:
                    if ser['is_monitor'] == False:
                        ser['is_monitor'] = True
                        rest_mon_num -= 1
                        if rest_mon_num <= 0:
                            break
        # Use mkcephfs to set up ceph system.
        LOG.info('server_list = %s' % server_list)
        monitor_node = self._select_monitor(context, server_list)
        LOG.info('Choose monitor node = %s' % monitor_node)
        # Clean ceph data.
        def __clean_data(host):
            self._agent_rpcapi.update_ssh_keys(context, host)
            self._agent_rpcapi.clean_ceph_data(context, host)

        def __create_crushmap(context, server_list, host):
            self._agent_rpcapi.create_crushmap(context,
                                               server_list=server_list,
                                               host=host)

        try:
            _update("Cleaning")
            thd_list = []
            for ser in server_list:
                thd = utils.MultiThread(__clean_data, host=ser['host'])
                thd_list.append(thd)
            utils.start_threads(thd_list)
            _update("Clean success")
        except:
            _update("ERROR: Cleaning")

        # When clean data, we also begin to create ceph.conf
        # and init osd in db.
        # Do not run with the same time as clean_data.
        # It maybe cleaned by clean_data.
        try:
            _update("Create ceph.conf")
            manifest_json = ManifestParser(FLAGS.cluster_manifest, False).format_to_json()
            ceph_conf_in_cluster_manifest = manifest_json['ceph_conf']
            LOG.info('ceph_conf_in_cluster_manifest==scheduler===%s'%ceph_conf_in_cluster_manifest)
            self._agent_rpcapi.inital_ceph_osd_db_conf(context,
                                                       server_list=server_list,
                                                       ceph_conf_in_cluster_manifest=ceph_conf_in_cluster_manifest,
                                                       host=monitor_node['host'])
            _update("Create ceph.conf success")
        except:
            _update("ERROR: ceph.conf")

        try:
            _update("create crushmap")
            # Then begin to create crush map file.
            create_crushmap = utils.MultiThread(__create_crushmap,
                                    context=context,
                                    server_list=server_list,
                                    host=monitor_node['host'])
            create_crushmap.start()
        except:
            _update("ERROR: crushmap")

        try:
            # Begin to mount disks on the mount_point.
            _update("Mount disks")
            def __mount_disk(host):
                self._agent_rpcapi.mount_disks(context, host)

            thd_list = []
            for ser in server_list:
                thd = utils.MultiThread(__mount_disk, host=ser['host'])
                thd_list.append(thd)
            utils.start_threads(thd_list)
            _update("Mount disks success")
        except:
            _update("ERROR: mount disk")

        # Generate monitor keyring file.
        try:
            _update("start montior")
            monitor_keyring = utils.gen_mon_keyring()
            def __write_monitor_keyring(host):
                self._agent_rpcapi.write_monitor_keyring(context,
                                                         monitor_keyring,
                                                         host)

            thd_list = []
            for ser in server_list:
                thd = utils.MultiThread(__write_monitor_keyring, host=ser['host'])
                thd_list.append(thd)
            utils.start_threads(thd_list)
            _update("start monitor success")
        except:
            _update("ERROR: start monitor")

        try:
            _update("Create keyring")
            self._track_monitors(context, server_list)

            # Here we use our self-define dir for ceph-monitor services.
            # So we need to create the key ring by command.
            self._agent_rpcapi.create_keyring(context,
                    host=monitor_node['host'])

            self._agent_rpcapi.upload_keyring_admin_into_db(context,
                    host=monitor_node['host'])

            def _update_keyring_from_db(host):
                self._agent_rpcapi.update_keyring_admin_from_db(context,
                        host=host)

            thd_list = []
            for ser in server_list:
                thd = utils.MultiThread(_update_keyring_from_db,
                                        host=ser['host'])
                thd_list.append(thd)
            utils.start_threads(thd_list)
            _update("Success: keyring")
        except:
            _update("ERROR: keyring")

        try:
            self._agent_rpcapi.prepare_osds(context,
                                            server_list,
                                            host=monitor_node['host'])

            # Begin to start osd service.
            _update('Start osds')
            def __start_osd(host):
                self._agent_rpcapi.start_osd(context, host)

            thd_list = []
            for ser in server_list:
                thd = utils.MultiThread(__start_osd, host=ser['host'])
                thd_list.append(thd)
            utils.start_threads(thd_list)
            _update('OSD success')
        except:
            _update("ERROR: start osd")

        # add mds service
        if mds_node:
            try:
                _update("Start mds")
                LOG.info('start mds services, host = %s' % mds_node['host'])
                self._agent_rpcapi.add_mds(context, host=mds_node['host'])
            except:
                _update("ERROR: mds")

        # Created begin to get ceph status
        try:
            _update('Ceph status')
            stat = self._agent_rpcapi.get_ceph_health(context,
                                                  monitor_node['host'])
        except:
            _update('ERROR: ceph -s')

        if stat == False:
            self._update_server_list_status(context,
                                            server_list,
                                            "Ceph Start Error")
            LOG.error('Ceph starting failed!')
            raise

        try:
            _update('Set crushmap')
            # Wait until it's created over.
            while create_crushmap.is_alive():
                time.sleep(1)

            def __set_crushmap(context, host):
                self._agent_rpcapi.set_crushmap(context,
                                                host)
            set_crushmap = utils.MultiThread(__set_crushmap,
                                             context=context,
                                             host=monitor_node['host'])
            set_crushmap.start()
        except:
            _update('ERROR: set crushmap')

        # add rgw service
        # TODO hardcode list as followed:
        # [rgw_instance_name, is_ssl, uid, display_name,
        # email, sub_user, access, key_type]
        if rgw_node:
            try:
                _update("Start rgw")
                LOG.info("start rgw service, host = %s" % rgw_node['host'])
                self._agent_rpcapi.rgw_create(context,
                                              name="radosgw.gateway",
                                              host=rgw_node['host'],
                                              keyring="/etc/ceph/keyring.radosgw.gateway",
                                              log_file="/var/log/ceph/radosgw.gateway.log",
                                              rgw_frontends="civetweb port=80",
                                              is_ssl=False,
                                              s3_user_uid="johndoe",
                                              s3_user_display_name="John Doe",
                                              s3_user_email="john@example.com",
                                              swift_user_subuser="johndoe:swift",
                                              swift_user_access="full",
                                              swift_user_key_type="swift")
            except:
                _update("ERROR: rgw")

        _update('Active')

        self._update_init_node(context, server_list)
        while set_crushmap.is_alive():
            time.sleep(1)
        self._agent_rpcapi.update_all_status(context,
            host=monitor_node['host'])
        self._agent_rpcapi.update_zones_from_crushmap_to_db(context,None,
            monitor_node['host'])
        self._agent_rpcapi.update_storage_groups_from_crushmap_to_db(context,None,
            monitor_node['host'])
        self._judge_drive_ext_threshold(context)
        self._update_drive_ext_threshold(context)
        return {'message':'res'}

    @utils.single_lock
    def refresh_osd_number(self, context):
        LOG.info(" Scheduler Refresh Osd num")
        server_list = db.init_node_get_all(context)

        active_monitor_list = []
        for monitor_node in server_list:
            if monitor_node['status'] == "Active" \
               and "monitor" in monitor_node['type']:
                active_monitor_list.append(monitor_node)

        # select an active monitor
        idx = random.randint(0, len(active_monitor_list)-1)
        active_monitor = active_monitor_list[idx]
        self._agent_rpcapi.refresh_osd_num(context, host=active_monitor['host'])

    @utils.single_lock
    def osd_remove(self, context, osd_id):
        # NOTE osd_id here stands for the DB item id in osd_states table.
        LOG.info('osd_remove osd_id = %s' % osd_id)
        osd = db.osd_state_get(context, osd_id)
        init_node = db.init_node_get_by_service_id(context, \
                                                   osd['service_id'])
        if init_node['status'] == 'Active':
            try:
                self._agent_rpcapi.osd_remove(context, osd_id, init_node['host'])
                self._agent_rpcapi.update_osd_state(context, init_node['host'])
            except rpc_exc.Timeout:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_remove rpc timeout')
                LOG.error('ERROR: osd_remove rpc timeout')
            except rpc_exc.RemoteError:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_remove rpc remote')
                LOG.error('ERROR: osd_remove rpc remote')
            except:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_remove')
                LOG.error('ERROR: osd_remove')
                raise
        else:
            return False

    @utils.single_lock
    def osd_restart(self, context, osd_id):
        LOG.info('scheduler manager:osd_restart')
        osd = db.osd_state_get(context, osd_id)
        init_node = db.init_node_get_by_service_id(context, \
                                                 osd['service_id'])
        if init_node['status'] == 'Active':
            try:
                self._agent_rpcapi.osd_restart(context, osd_id, init_node['host'])
                self._agent_rpcapi.update_osd_state(context, init_node['host'])
            except rpc_exc.Timeout:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_restart rpc timeout')
                LOG.error('ERROR: osd_restart rpc timeout')
            except rpc_exc.RemoteError:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_restart rpc remote error')
                LOG.error('ERROR: osd_restart rpc remote error')
            except:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_restart')
                LOG.error('ERROR: osd_restart')
                raise
        else:
            return False

    @utils.single_lock
    def osd_add(self, context, osd_id):
        LOG.info('scheduler manager:osd_add')
        osd = db.osd_state_get(context, osd_id)
        init_node = db.init_node_get_by_service_id(context, \
                                                 osd['service_id'])
        if init_node['status'] == 'Active':
            try:
                self._agent_rpcapi.osd_add(context, osd_id, init_node['host'])
                self._agent_rpcapi.update_osd_state(context, init_node['host'])
            except rpc_exc.Timeout:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_restart rpc timeout')
                LOG.error('ERROR: osd_add rpc timeout')
            except rpc_exc.RemoteError:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_restart rpc remote error')
                LOG.error('ERROR: osd_add rpc remote error')
            except:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_restart')
                LOG.error('ERROR: osd_add')
                raise
        else:
            return False

    @utils.single_lock
    def osd_restore(self, context, osd_id):
        LOG.info('osd_restoree osd_id = %s' % osd_id)
        osd = db.osd_state_get(context, osd_id)
        init_node = db.init_node_get_by_service_id(context,
                                                   osd['service_id'])
        if init_node['status'] == 'Active':
            LOG.debug('agent.rpcapi.osd_restore host = %s' % init_node['host'])
            try:
                self._agent_rpcapi.osd_restore(context, osd_id, init_node['host'])
                self._agent_rpcapi.update_osd_state(context, init_node['host'])
            except rpc_exc.Timeout:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_restore rpc timeout error')
                LOG.error('ERROR: osd_restore rpc timeout error')
                 
            except rpc_exc.RemoteError:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_restore rpc remote error')
                LOG.error('ERROR: osd_restore rpc remote error')
            except:
                #self._conductor_api.init_node_update_status_by_id(context,
                #    init_node['id'], 'ERROR: osd_restore')
                LOG.error('ERROR: osd_restore') 
                raise
        else:
            return False

    @utils.single_lock
    def osd_refresh(self, context):
        LOG.info('refresh osd status')
        active_server = self._get_active_server(context)
        return self._agent_rpcapi.osd_refresh(context, active_server['host'])

    @utils.single_lock
    def cluster_refresh(self, context):
        LOG.info('refresh cluster status')
        active_server = self._get_active_server(context)
        return self._agent_rpcapi.cluster_refresh(context, active_server['host'])

    def health_status(self, context):
        record = {}
        def _thd_fun(host):
            ret = self._agent_rpcapi.health_status(context,
                                                   host=host)
            record[host] = ret

        ceph_nodes = db.init_node_get_all(context)
        thd_list = []
        for ser in ceph_nodes:
            thd = utils.MultiThread(_thd_fun, host=ser['host'])
            thd_list.append(thd)

        utils.start_threads(thd_list)

        for v in record.values():
            if v.find('ERROR') == -1:
                return v
        return 'CRITICAL_ERROR'

    def _get_active_server(self, context):

        server_list = db.init_node_get_all(context)
        active_server_list = [x for x in server_list if x['status'] == "Active"]
        idx = random.randint(0, len(active_server_list)-1)
        return active_server_list[idx]

    def _set_active_server(self, context):
        values = {}
        values['status'] ='Active'
        server_list = db.init_node_get_all(context)
        server_id_list = [x.id for x in server_list ]
        #TODO modify to batch updating
        for server_id in server_id_list:
            db.init_node_update(context, server_id, values)
        active_server_list = server_list
        LOG.info('active_server_list===%s'%active_server_list)
        idx = random.randint(0, len(active_server_list)-1)
        LOG.info('idx===%s'%idx)
        return active_server_list[idx]

    def add_cache_tier(self, context, body):
        active_server = self._get_active_server(context)
        self._agent_rpcapi.add_cache_tier(context, body, active_server['host'])

    def remove_cache_tier(self, context, body):
        active_server = self._get_active_server(context)
        self._agent_rpcapi.remove_cache_tier(context, body,active_server['host'])

    def get_smart_info(self, context, body):
        ser = body['server']
        device = body['device_path']
        status = ser['status']
        host =  ser['host']
        if status == 'Active' or status == 'available':
            res = self._agent_rpcapi.get_smart_info(context, host, device)
            return res

    @utils.single_lock
    def monitor_restart(self, context, monitor_id):
        LOG.info('scheduler manager:monitor_restart')
        mon_obj = db.monitor_get(context,monitor_id)
        init_nodes = db.init_node_get_all(context)
        monitor_num = mon_obj.name
        mon_address = mon_obj.address.split(':')[0]
        #LOG.info('scheduler manager:monitor_restart--mon_address==%s'%mon_address)
        init_node = None
        for node in init_nodes:
            raw_ip = node.raw_ip.split(',')
            if mon_address in raw_ip:
                init_node = node
                LOG.info("scheduler manager:monitor_restart-- init_node['host']==%s"% init_node['host'])
                break
        if init_node['status'] == 'Active':
            try:
                self._agent_rpcapi.monitor_restart(context, monitor_num, init_node['host'])
            except rpc_exc.Timeout:
                LOG.error('ERROR: monitor_restart rpc timeout')
            except rpc_exc.RemoteError:
                LOG.error('ERROR: moitor_restart rpc remote error')
            except:
                LOG.error('ERROR: monitorrestart')
                raise
        else:
            return False

    def get_available_disks(self, context, body):
        server_id = body['server_id']
        server = db.init_node_get_by_id(context,id=server_id)
        status = server['status']
        if status == 'Active':
            res = self._agent_rpcapi.get_available_disks(context,server['host'])
            return res

    def add_new_disks_to_cluster(self, context, body):
        server_id = body.get('server_id',None)
        server_name = body.get('server_name',None)
        if server_id is not None:
            server = db.init_node_get_by_id(context,id=server_id)
        elif server_name is not None:
            server = db.init_node_get_by_host(context,host=server_name)
        self._agent_rpcapi.add_new_disks_to_cluster(context, body, server['host'])
        new_osd_count = int(server["data_drives_number"]) + len(body['osdinfo'])
        values = {"data_drives_number": new_osd_count}
        self._conductor_rpcapi.init_node_update(context,
                                        server["id"],
                                        values)

    def add_batch_new_disks_to_cluster(self, context, body):
        """

        :param context:
        :param body: {"disks":[
                                {'server_id':'1','osdinfo':[{'storage_group_id':
                                                            "weight":
                                                            "journal":
                                                            "data":},{}]},
                                {'server_id':'2','osdinfo':[{'storage_group_id':
                                                            "weight":
                                                            "journal":
                                                            "data":},{}]},
                            ]
                    }
        :return:
        """
        disks = body.get('disks',[])
        try:
            for disk_in_same_server in disks:
                self.add_new_disks_to_cluster(context, disk_in_same_server)
        except:
            return {"message":"data error"}
        return {"message": "success"}


    def reconfig_diamond(self, context, body):
        servers = db.init_node_get_all(context)
        for server in servers:
            if server['status'] == 'Active':
                self._agent_rpcapi.reconfig_diamond(context, body, server['host'])

    def add_storage_group_to_crushmap_and_db(self, context, body):
        '''

        :param context:
        :param body:{'storage_group': [{
                        'id':None,
                        'name': 'storage_group_name',
                        'friendly_name': 'storage_group_name',
                        'storage_class': 'storage_group_name',
                        'marker': '#FFFFF',
                        'rule_info':{
                                    'rule_name':'storage_group_name',
                                    'rule_id':None,
                                    'type':'replicated',
                                    'min_size':0,
                                    'max_size':10,
                                    'takes': [{'take_id':-12,
                                            'choose_leaf_type':'host',
                                            'choose_num':2,
                                            },
                                            ]
                                }
                        'cluster_id':1  //bad code. the origin is 1
                    },
                    ]
                }
        :return:
        '''
        LOG.info('add_storage_group_to_crushmap_and_db body=%s'%body)
        storage_groups = body.get('storage_group')
        cluster_id = body.get('cluster_id',None)
        active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
        LOG.info('sync call to host = %s' % active_monitor['host'])
        for storage_group in storage_groups:

            rule_info = storage_group['rule_info']
            LOG.info('add_storage_group_to_crushmap_and_db storage_group=%s'%rule_info)
            ret = self._agent_rpcapi.add_rule_to_crushmap(context, rule_info, active_monitor['host'])
            rule_id = ret.get('rule_id')
            take_order = 0
            #LOG.info('take==333333=====%s'%storage_group.get('take'))
            for take in storage_group.get('rule_info').get('takes'):
                storage_group_to_db = {
                    'name':storage_group['name'],
                    'storage_class':storage_group['storage_class'],
                    'friendly_name':storage_group['friendly_name'],
                    'marker':storage_group['marker'],
                    'rule_id':rule_id,
                    'take_id':take.get('take_id'),
                    'take_order':take_order,
                    'choose_type':take.get('choose_leaf_type'),#TODO
                    'choose_num':take.get('choose_num'),#"TODO"
                    'status':'IN',
                }
                #LOG.info('take==444444444=====%s'%storage_group_to_db)
                db.storage_group_update_or_create(context, storage_group_to_db)
                take_order += 1
        message = {'info':'Add storage group %s success!'%(','.join([ storage_group['name'] for storage_group in storage_groups])),
                   'error_code':'','error_msg':''}
        return message

    def update_storage_group_to_crushmap_and_db(self, context, body):
        LOG.info('update_storage_group_to_crushmap_and_db body=%s'%body)
        storage_groups = body.get('storage_group')
        cluster_id = body.get('cluster_id',None)
        active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
        LOG.info('sync call to host = %s' % active_monitor['host'])
        message = {'info':'Update success!','error_code':[],'error_msg':[]}
        for storage_group in storage_groups:
            rule_info = storage_group.get('rule_info')
            storage_group_in_db = db.storage_group_get_by_name(context,storage_group['name'])
            rule_id = storage_group_in_db['rule_id']
            pools = db.pool_get_by_ruleset(context,rule_id)
            if len(pools) > 0:
                db.update_storage_group_marker(context,storage_group['name'],storage_group['marker'])
                pool_names = [ pool['name'] for pool in pools ]
                #message['error_code'].append('-1')
                message['info'] = 'Storage group %s was used by pool %s currently and Only marker update success!'%(storage_group['name'],pool_names)
                continue
            ret = self._agent_rpcapi.modify_rule_in_crushmap(context, rule_info, active_monitor['host'])
            rule_id = ret.get('rule_id')
            take_order = 0
            LOG.info('update_storage_group_to_crushmap_and_db=====%s'%storage_group.get('take'))
            for take in storage_group.get('rule_info').get('takes'):
                storage_group_to_db = {
                    'name':storage_group['name'],
                    'storage_class':storage_group['storage_class'],
                    'friendly_name':storage_group['friendly_name'],
                    'marker':storage_group['marker'],
                    'rule_id':rule_id,
                    'take_id':take.get('take_id'),
                    'take_order':take_order,
                    'choose_type':take.get('choose_leaf_type'),#TODO
                    'choose_num':take.get('choose_num'),#"TODO"
                }
                LOG.info('update_storage_group_to_crushmap_and_db=====%s'%storage_group_to_db)
                db.storage_group_update_or_create(context, storage_group_to_db)
                take_order += 1
            db.storage_group_delete_by_order_and_name(context,take_order=take_order,name=storage_group['name'])
        message['error_code'] = ','.join(message['error_code'])
        message['error_msg'] = ','.join(message['error_msg'])
        LOG.info('---888--%s'%message)
        return message

    def update_zones_from_crushmap_to_db(self, context, body):
        if body is not None:
            cluster_id = body.get('cluster_id',None)
        else:
            cluster_id = None
        active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
        LOG.info('update_zones_from_crushmap_to_db sync call to host = %s' % active_monitor['host'])
        self._agent_rpcapi.update_zones_from_crushmap_to_db(context,body,active_monitor['host'])
        return {'message':'success'}

    def add_zone_to_crushmap_and_db(self, context, body):
        if body is not None:
            cluster_id = body.get('cluster_id',None)
        else:
            cluster_id = None
        active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
        LOG.info('add_zone_to_crushmap_and_db sync call to host = %s' % active_monitor['host'])
        self._agent_rpcapi.add_zone_to_crushmap_and_db(context,body,active_monitor['host'])
        return {'message':'success'}

    def get_default_pg_num_by_storage_group(self, context, body):
        if body is not None:
            cluster_id = body.get('cluster_id',None)
        else:
            cluster_id = None
        active_monitor = self._get_active_monitor(context, cluster_id=cluster_id)
        LOG.info('get_default_pg_num_by_storage_group sync call to host = %s' % active_monitor['host'])
        pg_num_default = self._agent_rpcapi.get_default_pg_num_by_storage_group(context,body,active_monitor['host'])
        return {'pg_num_default':pg_num_default}

    def rgw_create(self, context, server_name, rgw_instance_name, is_ssl,
                   uid, display_name, email, sub_user, access, key_type):
        host = server_name
        self._agent_rpcapi.rgw_create(context, host, server_name, rgw_instance_name,
                                      is_ssl, uid, display_name, email, sub_user,
                                      access, key_type)
