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

from vsm.exception import *

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

    def create_storage_pool(self, context, body=None):
        LOG.info('scheduler/manager.py create_storage_pool')
        active_monitor = self._get_active_monitor(context)

        LOG.info('sync call to host = %s' % active_monitor['host'])
        body['cluster_id'] = active_monitor['cluster_id']

        pool_ref = db.pool_get_by_name(context,
                                       body['name'],
                                       body['cluster_id'])
        if not pool_ref:
            self._agent_rpcapi.create_storage_pool(context, body)
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

        if len(monitor_list) < 3:
            LOG.error('There must be at least three monitors.')
            self._update_server_list_status(context,
                                            server_list,
                                            "Error: monitors < 3")
            try:
                raise MonitorAddFailed
            except Exception, e:
                LOG.error("%s: %s" %(e.code, e.message))
            raise

        LOG.info(' monitor_list = %s' % monitor_list)
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

    def _get_active_monitor(self, context, beyond_list=None):
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
            LOG.info("monitor_node:%s" % monitor_node)
            if monitor_node['status'] == "Active" \
               and monitor_node['type'].find('monitor') != -1:
                if not __is_in(monitor_node['host']):
                    active_monitor_list.append(monitor_node)
        if len(active_monitor_list) < 2:
            LOG.error('There must be 2 monitor in the cluster')
            try:
                raise MonitorException
            except:
                LOG.error("There must be 2 monitor in the monitor")
            return False

        # select an active monitor
        idx = random.randint(0, len(active_monitor_list)-1)
        return active_monitor_list[idx]

    def add_monitor(self, context, server_list):
        # monitor will be add
        new_monitor_list = [x for x in server_list if x['is_monitor']]
        LOG.info("new_monitor_list  %s" % new_monitor_list)
        if len(new_monitor_list) < 1:
            LOG.info("no monitor will be add")
            return True

        active_monitor = self._get_active_monitor(context)
        LOG.info("active_monitor:%s" % active_monitor)

        error_num = 0
        for ser in new_monitor_list:
            try:
                self._start_add(context, ser['id'])
                # get ceph_config
                ceph_config = self._get_ceph_config(context)

                # gen mon_id
                monitor_list = []
                for x in ceph_config:
                    if x.startswith("mon."):
                        monitor_list.append(int(x.replace("mon.","")))
                monitor_list.sort()

                deleted_times = db.cluster_get_deleted_times(context,
                                                             ser['cluster_id'])
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
            LOG.info("monitor_node:%s" % monitor_node)
            if monitor_node['status'] == "Active":
                if not __is_in(monitor_node['host']):
                    active_monitor_list.append(monitor_node)

        # select an active monitor
        idx = random.randint(0, len(active_monitor_list)-1)
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
        active_monitor = self._get_active_monitor(context)

        for ser in new_storage_list:
            try:
                self._start_add(context, ser['id'])
                # update zone_id
                values = {"zone_id": ser['zone_id']}
                self._conductor_rpcapi.init_node_update(context,
                                                        ser['id'],
                                                        values)
                # save ceph conf
                LOG.info(" start save ceph config to %s " % ser['host'])
                self._agent_rpcapi.update_ceph_conf(context, ser['host'])
                # save admin keyring
                LOG.info(" start save ceph keyring to %s " % ser['host'])
                self._agent_rpcapi.update_keyring_admin_from_db(context,
                                                                ser['host'])

                LOG.info('Begin to add osd in agent host = %s' % ser['host'])
                self._agent_rpcapi.add_osd(context,
                                           ser['id'],
                                           ser['host'])

                #update osd status, capacity, weight
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

        return True

    def remove_osd(self, context, server_list):
        remove_storage_list = [x for x in server_list if x['remove_storage']]
        LOG.info('removing storages %s ' % remove_storage_list)

        active_monitor = self._get_active_monitor(context)
        LOG.info('active_monitor = %s' % active_monitor['host'])

        for ser in remove_storage_list:
            try:
                self._start_remove(context, ser['id'])
                # remove storage
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

        active_monitor = self._get_active_monitor(context)
        LOG.info('active_monitor = %s' % active_monitor['host'])
        try:
            for ser in remove_storage_list:
                self._start_remove(context, ser['id'])
                # remove storage
                self._agent_rpcapi.remove_mds(context,
                                              ser['id'],
                                              active_monitor['host'])
                is_unavail = True if ser['status'] == 'unavailable' else False
                self._remove_success(context,
                                     ser['id'],
                                     "storage",
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
                     u'zone_id': u'1'},
                    {u'is_storage': True,
                     u'is_monitor': False,
                     u'id': u'2',
                     u'zone_id': u'2'}
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
                

        self._update_server_list_status(context, server_list, 'running')
        _update_ssh_key()

        self.add_monitor(context, server_list)

        # Begin to add osds.
        LOG.info("start to add storage")
        self.add_osd(context, server_list)

        self._judge_drive_ext_threshold(context)
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
            if ser['mds'] == 'yes':
                need_change_mds = True

        try:
            LOG.info("start to remove monitor")
            self.remove_monitors(context, server_list)

            LOG.info("start to remove storage")
            self.remove_osd(context, server_list)

            if need_change_mds:
                LOG.info("start to remove mds")
                self.remove_mds(context, server_list)
                self.add_mds(context, server_list)
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

        active_monitor = self._get_active_monitor(context)
        LOG.info("stop_server of scheduer manager %s" % server_list)
        for item in server_list:
            res = db.init_node_get(context, item['id'])
            self._start_stop(context, item['id'])
            try:
                self._agent_rpcapi.stop_server(context,
                                               item['id'],
                                               res['host'])

                self._agent_rpcapi.update_osd_state(context,
                                      active_monitor['host'])

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

        if need_change_mds:
            self.add_mds(context, server_list)
        return True

    @utils.single_lock
    def start_server(self, context, body=None):
        """Start all osd service, then start the server.
           body = {u'servers': [{u'cluster_id': 1, u'id': u'1'},
                        {u'cluster_id': 1, u'id': u'2'}]}
        """
        LOG.info("DEBUG in start server in scheduler manager.")
        server_list = body['servers']
        active_monitor = self._get_active_monitor(context)
        for item in server_list:
            res = db.init_node_get(context, item['id'])
            self._start_start(context, item['id'])
            try:
                self._agent_rpcapi.start_server(context, item['id'], res['host'])
                self._agent_rpcapi.update_osd_state(context, active_monitor['host'])
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
    def create_cluster(self, context, server_list):
        """Add the servers into ceph cluster.

        It's notable that, the type of body['servers']
        looks as below:

           [
               {u'is_storage': True,
                u'is_monitor': True,
                u'id': u'1',
                u'zone_id': u'1'},
               {u'is_storage': True,
                u'is_monitor': False,
                u'id': u'2',
                u'zone_id': u'2'}
           ]

        Here we also need to fetch info from DB.
        """
        # Add hostname here.
        for ser in server_list:
            ser_ref = db.init_node_get(context, ser['id'])
            ser['host'] = ser_ref['host']

        # Use mkcephfs to set up ceph system.
        monitor_node = self._select_monitor(context, server_list)
        LOG.info('Choose monitor node = %s' % monitor_node)

        def _update(status):
            LOG.debug('status = %s' % status)
            self._update_server_list_status(context,
                                            server_list,
                                            status)
            if status.lower().find('error') != -1:
                raise

        # Set at least 3 mons when creating cluster
        nums = len(server_list)
        if nums >= 3:
            count = 0
            rest_mon_num = 0
            for ser in server_list:
                if ser['is_monitor'] == True:
                    count += 1
            if count < 3:
                rest_mon_num = 3 - count
            if rest_mon_num > 0:
                for ser in server_list:
                    if ser['is_monitor'] == False:
                        ser['is_monitor'] = True
                        rest_mon_num -= 1
                        if rest_mon_num <= 0:
                            break

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
            self._agent_rpcapi.inital_ceph_osd_db_conf(context,
                                                       server_list=server_list,
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
        try:
            _update("Start mds")
            LOG.info('start mds services, host = %s' % monitor_node['host'])
            self._agent_rpcapi.add_mds(context, host=monitor_node['host'])
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
                _update('Active')
            set_crushmap = utils.MultiThread(__set_crushmap,
                                             context=context,
                                             host=monitor_node['host'])
            set_crushmap.start()
        except:
            _update('ERROR: set crushmap')

        self._update_init_node(context, server_list)
        while set_crushmap.is_alive():
            time.sleep(1)
        self._agent_rpcapi.update_all_status(context,
            host=monitor_node['host'])
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

    def add_cache_tier(self, context, body):
        active_server = self._get_active_server(context)
        self._agent_rpcapi.add_cache_tier(context, body, active_server['host'])

    def remove_cache_tier(self, context, body):
        active_server = self._get_active_server(context)
        self._agent_rpcapi.remove_cache_tier(context, body,active_server['host'])
