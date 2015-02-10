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

# pylint: disable=W0621

"""
Agent Service
"""
import random
import re
import os
import json
import time
from vsm import db
from vsm import context
from vsm import flags
from vsm import manager
from vsm import utils
from vsm import exception
from decorator import decorator
from vsm.openstack.common import log as logging
from vsm.openstack.common import timeutils
from vsm.conductor import rpcapi as conductor_rpcapi
from vsm.agent import driver
from vsm.agent import cephconfigparser
from vsm.manifest.parser import ManifestParser
from vsm.manifest import sys_info
from vsm.openstack.common.periodic_task import periodic_task
from vsm.openstack.common.rpc import common as rpc_exc
from vsm.agent import rpcapi as agent_rpc
from vsm import context
CTXT = context.get_admin_context()

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

#@decorator
#def require_active_host(func, *args, **kwargs):
#    init_node = db.init_node_get_by_host(args[0], FLAGS.host)
#    if init_node['status'] == "Active":
#        return func(*args, **kwargs)

def _get_interval_time(key):
    LOG.debug('get interval_time %s' % key)
    setting = db.vsm_settings_get_by_name(CTXT, key)
    if setting:
        LOG.debug('interval_time for %s : %s' % (key, setting.get('value')))
        return abs(int(setting.get('value', 30)))
    else:
        return 30

class AgentManager(manager.Manager):
    """Chooses a host to create storages."""

    RPC_API_VERSION = '1.2'

    def __init__(self, service_name=None, *args, **kwargs):
        #if not scheduler_driver:
        #    scheduler_driver = FLAGS.scheduler_driver
        #self.driver = importutils.import_object(scheduler_driver)
        super(AgentManager, self).__init__(*args, **kwargs)
        self._context = context.get_admin_context()
        self._driver = driver.DbDriver()
        self.ceph_driver = driver.CephDriver()
        self.crushmap_driver = driver.CreateCrushMapDriver()
        self._smp = ManifestParser()
        self._node_info = self._smp.format_to_json()
        #TODO (jiyou)
        # if conductor all is shutdown.
        # self._conductor_rpcapi = self.db
        self._conductor_rpcapi = conductor_rpcapi.ConductorAPI()
        self._agent_rpcapi = agent_rpc.AgentAPI()
        self._init_node_number = 0
        self._init_node_id = 0
        self._service_id = 0
        self._lan_list = []
        self.host = FLAGS.host
        self._is_update_ssh = False
        self._cluster_id = None
        self._is_init_ceph = False
        self._drive_num_count = 0

    def test_service(self, context):
        return {'status': 'ok'}

    def _get_cluster_ref(self):
        controller_ip = self._node_info['controller_ip']
        # Find cluster_ref below.
        # Set network info in dict.
        # TODO need to add cluster_get_by_controller_ip() in DB.
        # TODO need to add raw_ip in cluster table.
        right_ref = None
        cluster_list = db.cluster_get_all(self._context)
        for cluster_ref in cluster_list:
            if right_ref:
                break

            lan_list = [cluster_ref['primary_public_network'],
                       cluster_ref['secondary_public_network'],
                       cluster_ref['cluster_network']]

            LOG.info('Get vlan list = %s' % lan_list)

            for lan in lan_list:
                if utils.is_in_lan(controller_ip, lan):
                    right_ref = cluster_ref
                    self._lan_list = lan_list
                    break

        if not right_ref:
            LOG.info('Can not find the right cluster ref.')
        return right_ref

    def _set_net_add_seq(self, ip_dict):
        """Set the network info."""

        name_list = ['primary_public_ip',
                     'secondary_public_ip',
                     'cluster_ip']
        for pos,lan in enumerate(self._lan_list):
            for ip in self._node_info['ip'].split(','):
                if utils.is_in_lan(ip, lan):
                    ip_dict[name_list[pos]] = ip

        LOG.info('ip_dict = %s', ip_dict)

        return ip_dict

    def _write_info_into_devices(self):
        """Write info into devices."""
        device_dict = {}
        device_dict['service_id'] = self._service_id
        device_dict['state'] = 'MISSING'
        device_dict['fs_type'] = 'xfs'
        device_dict['total_capacity_kb'] = 0
        self._drive_num_count = 0

        for storage_class in self._node_info["storage_class"]:
            device_type = storage_class['name']
            storage_group_ref = db.storage_group_get_by_storage_class(self._context,
                                                                      device_type)
            if storage_group_ref:
                for disk in storage_class['disk']:
                    device_dict['journal'] = disk['journal']
                    device_dict['name'] = disk['osd']
                    device_dict['device_type'] = device_type
                    device_dict['mount_point'] = disk['osd']
                    device_dict['path'] = disk['osd']
                    self._drive_num_count += 1 
                    try:
                        device_ref = db.\
                            device_get_by_name_and_journal_and_service_id(\
                                    self._context,
                                    device_dict['name'],
                                    device_dict['journal'],
                                    device_dict['service_id'])
                        if not device_ref:
                            device_dict['used_capacity_kb'] = 0
                            device_dict['avail_capacity_kb'] = 0
                            db.device_create(self._context, device_dict)
                    except exception.UpdateDBError, e:
                        LOG.error('%s:%s' % (e.code, e.message))
            else:
                LOG.warn('The device type %s is not supported by this cluster.' % device_type)

    def _check_ip_address(self, values):
        """Check the ip address info, if failed, change it to be unavailble."""

        ip = values.get('primary_public_ip', None)
        if not ip:
            return False
        if len(ip.split('.')) != 4:
            return False

        ip = values.get('secondary_public_ip', None)
        if not ip:
            return False
        if len(ip.split('.')) != 4:
            return False

        ip = values.get('cluster_ip', None)
        if not ip:
            return False
        if len(ip.split('.')) != 4:
            return False
        return True

    def _restore_node_status(self, init_node):
        if init_node:
            node_id = init_node.get('id', None)
            status = init_node.get('status', None)
            pre_status = init_node.get('pre_status', None)
            if status == 'unavailable':
                # restore the server status.
                if pre_status == 'Active':
                    try:
                        # check if ceph daemons are up.
                        (stdout, stderr) = utils.execute('service', 'ceph', 'status', run_as_root=True)
                    except exception.ProcessExecutionError:
                        LOG.warn('The ceph daemon was not restored: %s' % stderr)
                elif pre_status == 'Stopped':
                    # Stop the ceph daemon if they are up. Restore the status to 'Stopped'
                    LOG.debug('Stop ceph daemon on host %s' % node_id)
                    utils.execute('service', 'ceph', 'stop', run_as_root=True)

                if pre_status in ('Active', 'Stopped', 'available'):
                    return True
            elif status == 'Stopped':
                # in case the status did not change when the server's up.
                # Stop the ceph daemon if they are up.
                LOG.debug('Stop ceph daemon on host %s' % node_id)
                utils.execute('service', 'ceph', 'stop', run_as_root=True)
        return False

    def insert_node_info_into_db(self):
        """Insert info into db."""
        # Get service id for init_node foreign key.
        if not self._service_id:
            service_ref = db.\
               service_get_by_host_and_topic(self._context,
                                             self.host,
                                             FLAGS.agent_topic)
            self._service_id = service_ref['id']

        self._write_info_into_devices()

        # Get cluster_id
        cluster_ref = self._get_cluster_ref()
        cluster_id = cluster_ref['id']
        self._cluster_id = cluster_id
        cluster_id_file = os.path.join(FLAGS.state_path, 'cluster_id')
        utils.write_file_as_root(cluster_id_file, self._cluster_id, 'w')
        # Get zone_id
        zone_ref = db.zone_get_by_name(self._context,
                                       self._node_info['zone'])
        if zone_ref:
            zone_id = zone_ref['id']
        else:
            LOG.error("Can't find the zone in DB!")
            raise

        values = {}
        values['service_id'] = self._service_id
        values['raw_ip'] = self._node_info['ip']
        self._set_net_add_seq(values)
        values['data_drives_number'] = self._drive_num_count

        ip_ready = self._check_ip_address(values)
        if ip_ready:
            values['status'] = 'available'
        else:
            values['status'] = 'Need More IP'
        values['mds'] = 'no'
        values['zone_id'] = zone_id
        values['type'] = self._node_info['role']
        values['host'] = self.host
        values['id_rsa_pub'] = self._node_info["id_rsa_pub"]
        values['raw_ip'] = self._node_info['ip']
        values['deleted'] = False
        #TODO cluster_id may be deleted.
        values['cluster_id'] = cluster_id
        values['weight'] = '1.0'
        init_node_ref = db.init_node_get_by_host(self._context,
                                                 self.host)

        # NOTE if status changed in DB. Do not update info.
        # If you update info of init_node,
        # It may cause error.
        if not init_node_ref:
            LOG.info(' create init_node ref = %s' %\
                json.dumps(values, sort_keys=True, indent=4))
            db.init_node_create(self._context, values)
        else:
            # Update the ip address information.
            values = {}
            values['id_rsa_pub'] = self._node_info["id_rsa_pub"]
            values['raw_ip'] = self._node_info['ip']
            self._set_net_add_seq(values)
            values['service_id'] = self._service_id
            values['data_drives_number'] = self._drive_num_count
            values['type'] = self._node_info['role']
            values['deleted'] = False
            if self._restore_node_status(init_node_ref):
                LOG.debug('Restore server %s status.' % init_node_ref['host'])
                values['status'] = init_node_ref['pre_status']
                if init_node_ref['status'].strip() != 'unavailable':
                    values['pre_status'] = init_node_ref['status']
            db.init_node_update(self._context, init_node_ref['id'], values)

        self._set_ssh_chanel()

        # TODO we just try to sync ceph.conf from db.
        try:
            self.update_ceph_conf(self._context)
        except:
            pass

    def update_ssh_keys(self, context):
        """When find new servers, insert new server's key."""
        if self._is_init_ceph:
            return

        self._is_update_ssh = True
        #TODO just insert new server's ssh key.
        try:
            self._set_ssh_chanel()
        except:
            LOG.info('Get error in update_ssh_keys')
        finally:
            self._is_update_ssh = False

    def _set_ssh_chanel(self):
        # Get self id from init_node table.
        init_node_id = self._conductor_rpcapi.init_node_get_by_host(
                            self._context,
                            self.host)['id']

        self._init_node_id = init_node_id

        # Get all the init nodes in the same cluster.
        node_list = self._conductor_rpcapi.init_node_get_cluster_nodes(
                            self._context,
                            init_node_id)

        self._init_node_number = len(node_list)

        # Write all the txt into ~/.ssh/authorized_keys
        fpath = FLAGS.ssh_authorized_keys

        content = utils.read_file_as_root(fpath)
        for node in node_list:
            key = node['id_rsa_pub']
            if content.find(key) != -1:
                continue
            key = key + "\n"
            utils.write_file_as_root(fpath, key)

        try:
            sys_info.wait_disk_ready(fpath)
        except exception.PathNotExist, e:
            LOG.info("Can't find authorized_keys!")
            LOG.error('%s:%s' %(e.code, e.message))

        utils.execute('chmod', '0700', fpath, run_as_root=True)

        etc_hosts = utils.read_file_as_root(FLAGS.etc_hosts)

        for node in node_list:
            hname = node['host']
            pri_ip = node['primary_public_ip']
            sed_ip = node['secondary_public_ip']
            thr_ip = node['cluster_ip']
            ip_list = [pri_ip, sed_ip, thr_ip]
            ip_list = [x for x in ip_list if x]
            LOG.info('host = %s ip = %s' % (hname, ip_list))

            find_error = False
            if etc_hosts.find(hname) == -1:
                find_error = True
                LOG.error('Can not find hname = %s in /etc/hosts' % hname)

            for ip in ip_list:
                if etc_hosts.find(ip) == -1:
                    find_error = True
                    LOG.error('Can not find ip = %s in /etc/hosts file' % ip)

            if find_error:
                LOG.error('Check /etc/hosts file failed.')
                utils.execute('service',
                              'vsm-agent',
                              'stop',
                              run_as_root=True)
                raise

    def init_host(self):
        #TODO Do not call ssh_key_here here.
        #TODO init_host is before the service_create_in_db()
        LOG.info('init_host in manager DEBUG')
        try:
            self.update_ceph_conf(self._context)
        except:
            LOG.info('Can not load ceph.conf now.')
        def _update_ceph_period():
            for i in range(1):
                try:
                    self.update_ceph_status(self._context)
                    time.sleep(10)
                except:
                    continue
        thd = utils.MultiThread(_update_ceph_period)
        thd.start()
        return 'test'

    def update_ceph_conf(self, context):
        LOG.info('agent/manager.py update ceph.conf from db.')
        cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        LOG.info('agent/manager.py update ceph.conf from db. OVER')

    def get_ceph_admin_keyring(self, context):
        return self.ceph_driver.get_ceph_admin_keyring(context)

    def save_ceph_admin_keyring(self, context, keyring_str):
        return self.ceph_driver.save_ceph_admin_keyring(context,
                                                        keyring_str)

    def update_pool_info(self, context, body=None):
        LOG.info('DEBUG in update_pool_info of agent manager.py')
        res = self._driver.update_pool_info(context)
        return res

    def update_recipe_info(self, context, body=None):
        LOG.info('DEBUG in update_recipe_info of agent manager.py')
        res = self._driver.update_recipe_info(context)
        return res

    def create_storage_pool(self, context, body=None):
        res = self.ceph_driver.create_storage_pool(context, body)
        return res

    def present_storage_pools(self, context, body=None):
        vsmapp_id = body['vsmapp_id']
        values = {'attach_status': 'success'}
        try:
            LOG.info(' PRESENT POOL BEGIN!')
            out, err = self.ceph_driver.present_storage_pools(context, body)
            LOG.info(' PRESENT POOL OVER!')
            pool_infos = body['pool_infos']
            for pinfo in pool_infos:
                sp_usage_ref = db.get_sp_usage_by_poolid_vsmappid(context, pinfo['id'], vsmapp_id)
                db.storage_pool_usage_update(context, sp_usage_ref['id'], values)

            LOG.info(' PRESENT POOL LOG = %s' % out)
            LOG.info(' PRESENT POOL ERR = %s' % err)
            return values
        except:
            LOG.info(' PRESENT POOL FAILED')
            values = {'attach_status': 'failed'}
            pool_infos = body['pool_infos']
            for pinfo in pool_infos:
                sp_usage_ref = db.get_sp_usage_by_poolid_vsmappid(context, pinfo['id'], vsmapp_id)
                db.storage_pool_usage_update(context, sp_usage_ref['id'], values)
            return values

    def _get_info_dict(self, context):
        """Get info dict from DB."""
        LOG.info('Get info_dict from DB.clusters')
        init_node_ref = self._conductor_rpcapi.\
                init_node_get_by_host(context, self.host)
        cluster_id = init_node_ref['cluster_id']

        info_dict = self._conductor_rpcapi.\
                cluster_info_dict_get_by_id(context, cluster_id)
        LOG.info(' info_dict = %s' % info_dict)
        return info_dict

    def update_keyring_admin_from_db(self, context):
        """Update /etc/ceph/keyring.admin file from DB."""
        LOG.info('update_keyring_admin_from_db()')
        try_times = 1
        info_dict = self._get_info_dict(context)
        while not info_dict:
            info_dict = self._get_info_dict(context)
            try_times = try_times + 1
            time.sleep(1)
            if try_times > 4:
                break

        keyring_admin = info_dict.get('keyring_admin', None)
        if keyring_admin:
            LOG.info(' get keyring from DB.')
            utils.write_file_as_root(FLAGS.keyring_admin, keyring_admin, "w")
            return True
        else:
            LOG.info('Can not get keyring, seend info not in DB.')
            return False

    def upload_keyring_admin_into_db(self, context):
        """upload keyring.admin cotent into DB.clusters table."""
        #NOTE we do not upload keyring in init_nodes table.
        #Because when one node wants to update it's keyring file.
        # 1. It does not know from which node to fetch the content.
        # 2. If there are multiple keyring file in init node.
        #    which one is the rignt one?
        utils.execute('chown', '-R', 'vsm:vsm', '/etc/ceph/',
                        run_as_root=True)
        if os.path.exists(FLAGS.keyring_admin):
            keyring_admin = open(FLAGS.keyring_admin, 'r').read()
        else:
            LOG.info('Can not find keyring in this host')
            try:
                raise exception.PathNotExist
            except exception.PathNotExist, e:
                LOG.error("%s: %s" %(e.code, e.message))
            return

        init_node_ref = self._conductor_rpcapi.\
             init_node_get_by_host(context, self.host)
        cluster_id = init_node_ref['cluster_id']
        values = {}
        values['info_dict'] = {'keyring_admin': keyring_admin}
        self._conductor_rpcapi.cluster_update(context,
                cluster_id, values)

    def mkcephfs(self, context):
        self._is_init_ceph = True
        try_times = 0
        while self._is_update_ssh:
            time.sleep(1)
            try_times = try_times + 1
            LOG.info('Wait for update ssh keys.')
            if try_times > 60:
                break

        status = self.ceph_driver.mkcephfs()
        LOG.info('Begin to update keyring admin into DB.')
        self.upload_keyring_admin_into_db(context)
        LOG.info('End to update keyring admin into DB.')
        self._is_init_ceph = False
        return status

    def update_all_status(self, context):
        def _try_pass(func):
            try:
                func(context)
            except:
                pass
        _try_pass(self.update_summary)
        _try_pass(self.update_pool_status)
        _try_pass(self.update_osds_status)
        _try_pass(self.update_osds_weight)
        _try_pass(self.update_device_capacity)
        _try_pass(self.update_rbd_status)
        _try_pass(self.update_pool_stats)
        _try_pass(self.update_mds_status)
        _try_pass(self.update_pg_and_pgp)
        _try_pass(self.update_pg_status)
        _try_pass(self.update_pool_usage)
        _try_pass(self.update_mon_health)
        _try_pass(self.update_server_status)
        _try_pass(self.update_ceph_status)

    def add_osd(self, context, host_id):
        return self.ceph_driver.add_osd(context, host_id)

    def add_monitor(self, context, host_id, mon_id):
        res = self.ceph_driver.add_monitor(context, host_id, mon_id)
        time.sleep(15)
        LOG.info("update mon health begin")
        self.update_mon_health(context)
        LOG.info("update mon health end")
        return res

    def remove_mds(self, context, host_id):
        return self.ceph_driver.remove_mds(context, host_id)

    def remove_osd(self, context, host_id):
        return self.ceph_driver.remove_osd(context, host_id)

    def cluster_id(self, context):
        return self._cluster_id

    def remove_monitor(self, context, host_id):
        ret = self.ceph_driver.remove_monitor(context, host_id)
        # Create a delete monitor record in init_nodes.
        # When add monitor, the new monitor id should be:
        # Non-used + num(DEL_MON)_in_db
        info_dict = db.cluster_info_dict_get_by_id(context, self._cluster_id)
        db.cluster_increase_deleted_times(context, self._cluster_id)
        self._sync_mon_list(context)
        return ret

    def get_ceph_config(self, context):
        return self.ceph_driver.get_ceph_config(context)

    def save_ceph_config(self, context, config):
        return self.ceph_driver.save_ceph_config(context, config)

    def start_monitor(self, context):
        # Start all the monitors
        return self.ceph_driver.start_monitor(context)

    def add_mds(self, context):
        return self.ceph_driver.add_mds(context)

    def start_mds(self, context):
        return self.ceph_driver.start_mds(context)

    def start_osd(self, context):
        return self.ceph_driver.start_osd(context)

    def start_ceph(self, context):
        return self.ceph_driver.start_ceph(context)

    def start_osd_daemon(self, context, num):
        return self.ceph_driver.start_osd_daemon(context, num)

    def get_ceph_health(self, context):
        return self.ceph_driver.get_ceph_health(context)

    def get_osds_total_num(self, context):
        return self.ceph_driver.get_osds_total_num()

    def clean_ceph_data(self, context):
        cluster_ref = db.cluster_get(context, self._cluster_id)
        file_system = cluster_ref['file_system']
        devices = db.device_get_all_by_service_id(context, self._service_id)
        journal_disks = []
        osd_disks = []
        for dev in devices:
            osd_disks.append(dev['name'])
            journal_disks.append(dev['journal'])
        return self.ceph_driver.clean_ceph_data(context,
                                                osd_disks,
                                                journal_disks,
                                                file_system)

    def mount_disks(self, context):
        cluster_ref = db.cluster_get(context, self._cluster_id)
        file_system = cluster_ref['file_system']
        devices = db.device_get_all_by_service_id(context,
                                                  self._service_id)
        return self.ceph_driver.mount_disks(devices, file_system)

    def _get_mon_id(self):
        # Get monitor id
        mon_id = None
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config_dict = config.as_dict()
        for section in config_dict:
            if section.startswith("mon."):
                if config_dict[section]['host'] == FLAGS.host:
                    mon_id = section.replace("mon.", "")
        return mon_id

    def write_monitor_keyring(self, context, monitor_keyring):
        utils.write_file_as_root('/etc/ceph/ceph.mon.keyring',
                                 monitor_keyring,
                                 'w')
        utils.execute('mkdir',
                      '-p',
                      '/var/lib/ceph/tmp',
                      run_as_root=True)

        mon_id = self._get_mon_id()

        if not mon_id:
            LOG.info('Not monitor node, skip start montior service.')
            return {'status': 'ok'}

        """
        Steps to start monitor service.
        cp -rf /etc/ceph/ceph.mon.keyring /var/lib/ceph/tmp/ceph$1.mon.keyring
        ceph-mon --cluster ceph \
                 --mkfs -i $1 \
                 --keyring /var/lib/ceph/tmp/ceph$1.mon.keyring

        mkdir -p  /var/lib/ceph/mon/mon$1
        cp -rf /etc/ceph/ceph.mon.keyring /var/lib/ceph/mon/mon$1/keyring
        echo "" > /var/lib/ceph/mon/mon$1/done
        echo "" > /var/lib/ceph/mon/mon$1/sysvinit
        service ceph -c /etc/ceph/ceph.conf start mon.$1
        """

        # copy montior keyring to each directory.
        utils.execute('mkdir',
                      '-p',
                      '/var/lib/ceph/mon/mon%s/' % mon_id,
                      run_as_root=True)
        utils.execute('mkdir',
                      '-p',
                      '/var/lib/ceph/tmp/',
                      run_as_root=True)

        utils.execute('cp',
                      '-rf',
                      '/etc/ceph/ceph.mon.keyring',
                      '/var/lib/ceph/tmp/ceph%s.mon.keyring' % mon_id,
                      run_as_root=True)

        utils.execute('cp',
                      '-rf',
                      '/etc/ceph/ceph.mon.keyring',
                      '/var/lib/ceph/tmp/ceph%s.mon.keyring' % mon_id,
                      run_as_root=True)

        utils.execute('ceph-mon',
                      '--cluster', 'ceph',
                      '--mkfs',
                      '-i', mon_id,
                      '--keyring',
                      '/var/lib/ceph/tmp/ceph%s.mon.keyring' % mon_id,
                      run_as_root=True)

        utils.execute('mkdir',
                      '-p',
                      '/var/lib/ceph/mon/mon%s' % mon_id,
                      run_as_root=True)

        utils.execute('touch',
                      '/var/lib/ceph/mon/mon%s/done' % mon_id,
                      run_as_root=True)

        utils.execute('touch',
                      '/var/lib/ceph/mon/mon%s/sysvinit' % mon_id,
                      run_as_root=True)

        utils.execute('service',
                      'ceph',
                      '-c', '/etc/ceph/ceph.conf',
                      'start', 'mon.%s' % mon_id,
                      run_as_root=True)
        return {'status': 'start_monitor_over'}

    def track_monitors(self, context):
        """Tracking monitor status for ceph.

        Return if monitors are in quorum?
        """
        return self.ceph_driver.track_monitors(self._get_mon_id())

    def create_keyring(self, context):
        """Create admin.keyring and bootstrap-type keyrings."""
        return self.ceph_driver.create_keyring(self._get_mon_id())

    def _get_osd_id(self, host=FLAGS.host):
        # Get monitor id
        osd_id_list = []
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config_dict = config.as_dict()
        for section in config_dict:
            if section.startswith("osd."):
                if config_dict[section]['host'] == host:
                    osd_id = section.replace("osd.", "")
                    osd_id_list.append(osd_id)

        return osd_id_list

    def prepare_osds(self, context, server_list):
        for ser in server_list:
            #utils.execute('ceph', 'osd', 'crush',
            #              'add-bucket', ser['host'],
            #              'host', run_as_root=True)

            #utils.execute('ceph', 'osd', 'crush',
            #              'move', ser['host'],
            #              'root=default', run_as_root=True)
            for osd in self._get_osd_id(ser['host']):
                LOG.info('osd = %s for %s' % (osd, ser['host']))
                utils.execute('ceph',
                              'osd',
                              'create',
                              run_as_root=True)

    def create_crushmap(self, context, server_list):
        return self.crushmap_driver.create_crushmap(context, server_list)

    def set_crushmap(self, context):
        return self.crushmap_driver.set_crushmap(context)

    def add_new_zone(self, context, zone_name):
        return self.crushmap_driver.add_new_zone(context, zone_name)

    def start_server(self, context, node_id):
        return self.ceph_driver.start_server(context, node_id)

    def stop_server(self, context, node_id):
        return self.ceph_driver.stop_server(context, node_id)

    def stop_mds(self, context):
        return self.ceph_driver.stop_mds(context)

    def refresh_osd_number(self, context):
        return self.ceph_driver.refresh_osd_number(context)

    def osd_remove(self, context, osd_id):
        def _update_osd_db():
            value= {}
            value['id'] = osd_id
            value['osd_name'] = 'osd.x'
            value['state'] = 'Out-Down'
            value['operation_status'] = FLAGS.vsm_status_removed
            db.osd_state_update(context, osd_id, value)

        def _update_device_db():
            value = {}
            value['id'] = osd['device']['id']
            value['total_capacity_kb'] = 0
            value['used_capacity_kb'] = 0
            value['avail_capacity_kb'] = 0
            db.device_update(context, osd['device']['id'], value)

        osd = db.osd_get(context, osd_id)
        osd_inner_id = osd['osd_name'].split('.')[-1]
        umount_path = osd['device']['name']
        self.ceph_driver.osd_remove(context,
                                    osd_inner_id,
                                    osd.get('device'),
                                    umount_path)
        _update_osd_db()
        _update_device_db()
        return True

    def osd_restart(self, context, osd_id):
        self.ceph_driver.osd_restart(context, osd_id)
        return True

    def osd_restore(self, context, osd_id):
        self.ceph_driver.osd_restore(context, osd_id)
        return True

    def osd_refresh(self, context):
        LOG.info("refresh osd status")
        self.update_osd_state(context)
        return True

    def cluster_refresh(self, context):
        LOG.info("refresh all status")
        self.update_all_status(context)
        return True

    def _get_cluster_id(self, context):
        init_node = db.init_node_get_by_host(context, FLAGS.host)
        return init_node['cluster_id']

    def get_pool_id_by_name(self, context, name):
        pools = self.ceph_driver.get_pool_stats()
        for pool in pools:
            if pool['pool_name'] == name:
                return pool['pool_id']
        return None

    def set_pool_pg_pgp_num(self, context, pool, pg_num, pgp_num):
        self.ceph_driver.set_pool_pg_pgp_num(context, pool, pg_num, pgp_num)
        return True

    @utils.pass_lock('d7f6685d-a90b-4a69-b178-4b8119a5bdde')
    def update_osd_state(self, context):
        self.update_osds_weight(context)
        self.update_device_capacity(context)
        self.update_osds_status(context)
        self.update_summary(context, sum_type=FLAGS.summary_type_osd)

    @utils.pass_lock('4663a886-1faf-4eed-9927-8d76d49ae8f3')
    def update_pool_state(self, context):
        self.update_pool_stats(context)
        self.update_pool_usage(context)
        self.update_pool_status(context)

    #@require_active_host
    @periodic_task(service_topic=FLAGS.agent_topic,
                   spacing=_get_interval_time('ceph_osd_dump'))
    def update_osds_status(self, context):
        osd_json = self.ceph_driver.get_osds_status()
        if osd_json is None:
            return None
        osd_dict = json.loads(osd_json)
        osd_list = osd_dict['osds']
        for osd in osd_list:
            osd_num = osd['osd']
            osd_name = 'osd.' + (str(osd_num))
            if osd['in'] and osd['up']:
                osd_status = FLAGS.osd_in_up
            elif osd['in'] and not osd['up']:
                osd_status = FLAGS.osd_in_down
            elif not osd['in'] and osd['up']:
                osd_status = FLAGS.osd_out_up
            else:
                if FLAGS.osd_state_autoout in osd['state']:
                    osd_status = FLAGS.osd_out_down_autoout
                else:
                    osd_status = FLAGS.osd_out_down
            values = {}
            values['osd_name'] = osd_name
            values['state'] = osd_status
            self._conductor_rpcapi.\
                osd_state_update(context, values)

    #@require_active_host
    @periodic_task(run_immediately=True, service_topic=FLAGS.agent_topic,
                   spacing=_get_interval_time('ceph_osd_tree'))
    def update_osds_weight(self, context):
        weight_list = self.ceph_driver.get_osds_tree()
        #LOG.debug('osd tree : %s' % weight_list)
        osd_states = db.osd_state_get_all(context)
        #LOG.debug('osd_state info : %s' % osd_states)
        if osd_states:
            #LOG.debug('Update crush weight.')
            osd_names = [osd.osd_name for osd in osd_states]
            for osd in weight_list:
                name = osd.get('name')
                if name and name in osd_names:
                    values = dict()
                    values['osd_name'] = name
                    values['weight'] = osd.get('crush_weight')
                    #LOG.debug('update crush weight values: %s' % values)
                    self._conductor_rpcapi.\
                        osd_state_update_or_create(context, values, create=False)

    #@require_active_host
    @periodic_task(run_immediately=True, service_topic=FLAGS.agent_topic,
                   spacing=_get_interval_time('ceph_pg_dump_osds'))
    def update_device_capacity(self, context):
        capacity_list = self.ceph_driver.get_osd_capacity()
        #LOG.debug('capacity list : %s' % capacity_list)
        devices = db.device_get_all(context)

        if devices:
            #LOG.debug('Update osd capacity.')
            #device_names = dict([(dev.get('name'), dev.get('id')) for dev in devices])
            #LOG.debug('device id and name dict: %s' % device_names)
            osd_states = db.osd_state_get_all(context)
            osd_names = dict([(osd_state.get('osd_name'), osd_state.get("device_id"))
                              for osd_state in osd_states])
            #LOG.debug('device id and osd name dict: %s' % osd_names)
            for osd in capacity_list:
                osd_id = osd.get('osd', None)
                if isinstance(osd_id, int):
                    osd_name = 'osd.' + (str(osd_id))
                    #LOG.debug('osd name in db %s' % osd_name)
                    if osd_name in osd_names.keys():
                        values = dict()
                        values['id'] = osd_names.get(osd_name)
                        values['total_capacity_kb'] = osd.get('kb')
                        values['used_capacity_kb'] = osd.get('kb_used')
                        values['avail_capacity_kb'] = osd.get('kb_avail')
                        #LOG.debug('update device capacity values: %s' % values)
                        self._conductor_rpcapi.\
                            device_update_or_create(context, values, create=False)

    def _compute_pg_num(self, context, osd_num, replication_num):
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

    @periodic_task(run_immediately=True,
                   service_topic=FLAGS.agent_topic,
                   spacing=FLAGS.reset_pg_heart_beat)
    def update_pg_and_pgp(self, context):
        db_pools = db.pool_get_all(context)
        for pool in db_pools:
            storage_group = db.storage_group_get_by_rule_id(context, \
                                                    pool['crush_ruleset'])
            if storage_group:
                osd_num_per_group = db.osd_state_count_by_storage_group_id(context, storage_group['id'])
                #reset pgs
                if 20 * osd_num_per_group > pool['pg_num']:
                    pg_num = self._compute_pg_num(context, osd_num_per_group, pool['size'])   
                    LOG.info("storage group id %s has %s osds" % (storage_group['id'], osd_num_per_group))
                    if osd_num_per_group > 64:
                        osd_num_per_group = 64
                        LOG.info("osd_num_per_group > 64, use osd_num_per_group=64")
                    step_max_pg_num = osd_num_per_group * 32
                    max_pg_num = step_max_pg_num + pool['pg_num']
                    if pg_num > max_pg_num:
                        pgp_num = pg_num = max_pg_num 
                        self.set_pool_pg_pgp_num(context, pool['name'], pg_num, pgp_num)
                    elif pg_num > pool['pg_num']:
                        pgp_num = pg_num
                        self.set_pool_pg_pgp_num(context, pool['name'], pg_num, pgp_num)
                    else:
                        continue

        ceph_pools = self.ceph_driver.get_pool_status()
        for pool in ceph_pools:
            values = {
                'pg_num': pool.get('pg_num'),
                'pgp_num': pool.get('pg_placement_num') 
                }
            db.pool_update_by_pool_id(context, pool['pool'], values) 

    #@require_active_host
    @periodic_task(run_immediately=True,
                   service_topic=FLAGS.agent_topic,
                   spacing=_get_interval_time('ceph_osd_dump'))
    def update_pool_status(self, context):
        ceph_list = self.ceph_driver.get_pool_status()
        cluster_id = self._get_cluster_id(context)
        db_pools = self._conductor_rpcapi.list_storage_pool(context)

        db_names = [pool.get('name') for pool in db_pools.values()]
        ceph_names = [pool.get('pool_name') for pool in ceph_list]

        # pools in db. Not in ceph.
        # Delete it.
        deleted_pools = set(db_names) - set(ceph_names)
        for pool_name in deleted_pools:
            LOG.info('Pool in DB, not in ceph, delete %s.' % pool_name)
            self._conductor_rpcapi.destroy_storage_pool(context, pool_name)

        # Pools in ceph, not int db.
        # Add it.
        add_pools = set(ceph_names) - set(db_names)
        for pool_name in add_pools:
            # if is in ceph, not in db.
            # and not created by vsm.
            for pool in ceph_list:
                if pool['pool_name'] == pool_name:
                    storage_group = db.storage_group_get_by_rule_id(context, \
                                                    pool.get('crush_ruleset'))
                    values = {
                        'pool_id': pool.get('pool'),
                        'name': pool.get('pool_name'),
                        'pg_num': pool.get('pg_num'),
                        'pgp_num': pool.get('pg_placement_num'),
                        'size': pool.get('size'),
                        'min_size': pool.get('min_size'),
                        'crush_ruleset': pool.get('crush_ruleset'),
                        'crash_replay_interval': pool.get('crash_replay_interval')
                    }
                    values['created_by'] = 'ceph'
                    values['cluster_id'] = cluster_id
                    values['tag'] = 'SYSTEM'
                    values['status'] = 'running'
                    if storage_group:
                        values['primary_storage_group_id'] = storage_group['id']
                    LOG.debug('Pool %s in ceph, not in db, add it.' % values)
                    self._conductor_rpcapi.create_storage_pool(context, values)

        for pool in ceph_list:
            values = {}
            if pool.get('pg_num') > pool.get('pg_placement_num'):
                self.ceph_driver.set_pool_pgp_num(context, pool['pool_name'], pool['pg_num'])
                values['pg_num'] = pool['pg_num']
                values['pgp_num'] = pool['pg_num']
            if pool.get('erasure_code_profile'):
                values['ec_status'] = pool['erasure_code_profile']
            if values:
                db.pool_update_by_pool_id(context, pool['pool'], values) 

        # If both in ceph/db. Update info in db.
        upd_pools = []
        for p in ceph_list:
            if p['pool_name'] in db_names:
                upd_pools.append(p)

        for pool in upd_pools:
            values = {
               'pool_id': pool.get('pool'),
               'name': pool.get('pool_name'),
               'pg_num': pool.get('pg_num'),
               'pgp_num': pool.get('pg_placement_num'),
               'size': pool.get('size'),
               'min_size': pool.get('min_size'),
               'crush_ruleset': pool.get('crush_ruleset'),
               'crash_replay_interval': pool.get('crash_replay_interval')
            }
            self._conductor_rpcapi.update_storage_pool_by_name(context,
                pool.get('pool_name'), cluster_id, values)

    #@require_active_host
    @periodic_task(run_immediately=True,
                   service_topic=FLAGS.agent_topic,
                   spacing=_get_interval_time('rbd_ls_-l_{pool_name}'))
    def update_rbd_status(self, context):
        rbd_list = self.ceph_driver.get_rbd_status()
        if rbd_list:
            rbd_list = rbd_list[:100]
            for rbd in rbd_list:
                db.rbd_update_or_create(context, rbd)

    #@require_active_host
    @periodic_task(run_immediately=True, service_topic=FLAGS.agent_topic,
                   spacing=_get_interval_time('ceph_osd_pool_stats'))
    def update_pool_stats(self, context):
        pool_stats = self.ceph_driver.get_pool_stats()
        #TODO: need to list pools by cluster id
        pools = self._conductor_rpcapi.list_storage_pool(context)
        if pools:
            #LOG.debug('Update pool stats.')
            pool_ids = [pool.get('pool_id') for pool in pools.values()]
            for stat in pool_stats:
                pid = stat.get('pool_id')
                if pid in pool_ids:
                    values = stat.get('client_io_rate')
                    if values:
                        values['pool_id'] = pid
                        #LOG.debug('pool stats values %s ' % values)
                        self._conductor_rpcapi.update_storage_pool(context, pid, values)
                    else:
                        LOG.info('No client io rate update for pool %s.' % pid)

    #@require_active_host
    @periodic_task(run_immediately=True,
                   service_topic=FLAGS.agent_topic,
                   spacing=_get_interval_time('ceph_mds_dump'))
    def update_mds_status(self, context):
        mds_list = self.ceph_driver.get_mds_status()
        if mds_list:
            for mds in mds_list:
                db.mds_update_or_create(context, mds)

    #@require_active_host
    #@periodic_task(run_immediately=True,
    #               service_topic=FLAGS.agent_topic,
    #               spacing=_get_interval_time('ceph_pg_dump_pgs_brief'))
    def update_pg_status(self, context):
        pg_list = self.ceph_driver.get_pg_status()
        if pg_list:
            for pg in pg_list:
                db.pg_update_or_create(context, pg)

    #@require_active_host
    @periodic_task(run_immediately=True, service_topic=FLAGS.agent_topic,
                   spacing=_get_interval_time('ceph_pg_dump_osds'))
    def update_pool_usage(self, context):
        pool_usage = self.ceph_driver.get_pool_usage()
        #TODO: need to list pools by cluster id
        pools = self._conductor_rpcapi.list_storage_pool(context)
        if pools:
            #LOG.debug('Update pool usage.')
            pool_ids = [pool.get('pool_id') for pool in pools.values()]
            for usage in pool_usage:
                pid = usage.get('poolid')
                if pid in pool_ids:
                    values = usage.get('stat_sum')
                    if values:
                        values['pool_id'] = pid
                        #LOG.debug('pool usage values %s ' % values)
                        self._conductor_rpcapi.update_storage_pool(context, pid, values)
                    else:
                        LOG.info('No stat sum for pool %s.' % pid)
                else:
                    LOG.info('pool %s does not exist in the existing pool list.' % pid)

    #@require_active_host
    @periodic_task(run_immediately=True, service_topic=FLAGS.agent_topic, 
                   spacing=_get_interval_time('ceph_status'))
    def update_mon_health(self, context):
        ceph_status = self.ceph_driver.get_ceph_status()
        LOG.debug(ceph_status)
        mons_address = dict([(x['name'], x['addr']) for x in ceph_status.get('monmap').get('mons')])
        health_stat = self.ceph_driver.get_mon_health()
        LOG.debug(health_stat)
        if health_stat:
            mon_stat = health_stat.get('timechecks').get('mons')
            mon_health = health_stat.get('health').get('health_services')[0].get('mons')
            LOG.debug("mon stat: %s \t\n mon health: %s" % (mon_stat, mon_health))

            if mon_stat and mon_health:
                for health in mon_health:
                    for stat in mon_stat:
                        if health.get('name') == stat.get('name'):
                            health.pop('health')
                            stat.update(health)
                            name = health.get('name')
                            if name in mons_address:
                                stat['address'] = mons_address[name]
                            # The interface will create a new monitor if it does not exist.
                            LOG.debug('update monitor health values: %s' % stat)
                            stat.setdefault("details", "-") # fix #216
                            db.monitor_update(context, health.get('name'), stat)

                # del mon which has been moved
                monitor_names_in_db = [mon.name for mon in db.monitor_get_all(context)]
                monitor_names_in_ceph = [stat.get('name') for stat in mon_stat]
                for mon_name in (set(monitor_names_in_db) - set(monitor_names_in_ceph)):
                    db.monitor_destroy(context, mon_name)

                # unhealth mon
                mons = ceph_status.get("monmap").get("mons")
                for mon in mons:
                    if not mon.get("name") in monitor_names_in_ceph:
                        mon['skew'] = 0
                        mon['latency'] = 0
                        mon['health'] = "-"
                        db.monitor_update(context, mon.get('name'), mon)

    def _sync_mon_list(self, context):
        try:
            ceph_status = self.ceph_driver.get_ceph_status()
            monitor_names_in_ceph = [x['name'] for x in ceph_status['monmap']['mons']]
            monitor_names_in_db = [mon.name for mon in db.monitor_get_all(context)]
            LOG.debug(monitor_names_in_ceph)
            LOG.debug(monitor_names_in_db)
            for mon_name in (set(monitor_names_in_db) - set(monitor_names_in_ceph)):
                db.monitor_destroy(context, mon_name)
        except:
            pass

    def update_summary(self, context, sum_type=None):
        cluster_id = self._get_cluster_id(context)
        sum_dict = self.ceph_driver.get_ceph_status()
        health_list = self.ceph_driver.get_ceph_health_list()
        sum_dict['health_list'] =  health_list
        sum_opts = [ opt.default for opt in flags.summary_type_opts ]
        sum_types = []

        if sum_type:
            if sum_type in sum_opts:
                sum_types.append(sum_type)
            else:
                LOG.warn('Invalid summary option type: %s.' % sum_type)
                return
        else:
            sum_types = sum_opts

        if cluster_id and sum_dict:
            for typ in sum_types:
                sum_map = self.ceph_driver.get_summary(typ, sum_dict)
                if sum_map:
                    val = {'summary_data': sum_map}
                    db.summary_update(context, cluster_id, typ, val)
                    if typ.find('cluster') != -1:
                        db.summary_update(context, cluster_id, 'ceph', val)

    @periodic_task(service_topic=FLAGS.agent_topic, spacing=FLAGS.server_ping_time)
    def update_server_status(self, context):
        """Update server status in every 5 seconds."""
        def _try_connect(host):
            try:
                self._agent_rpcapi.test_service(context,
                                                FLAGS.agent_topic,
                                                host)
                return True
            except rpc_exc.Timeout, rpc_exc.RemoteError:
                return False
            except:
                return False

        def _thread_func_for_unavailable(host, node_id, pre_status):
            if _try_connect(host):
                db.init_node_update_status_by_id(context,
                                                 node_id,
                                                 pre_status)
            else:
                for i in range(10):
                    if _try_connect(host):
                        db.init_node_update_status_by_id(context,
                                                         node_id,
                                                         pre_status)
                        break

        def _thread_func_for_other(host, node_id, pre_status):
            if not _try_connect(host):
                error_num = 0
                for i in range(10):
                    if not _try_connect(host):
                        error_num += 1
                if error_num > 8:
                    db.init_node_update_status_by_id(context,
                                                     node_id,
                                                     'unavailable')

        nodes = db.init_node_get_all(context)
        unav_list = []
        health_list = []
        for node in nodes:
            if not node.get('host', None):
                continue

            if node.get('status', None) == 'unavailable':
                unav_list.append(node)
            else:
                health_list.append(node)

        nav_list = []
        for node in unav_list:
            host = node.get('host', None)
            node_id = node.get('id', None)
            pre_status = node.get('pre_status', None)
            thd = utils.MultiThread(_thread_func_for_unavailable,
                                    host, node_id, pre_status)
            nav_list.append(thd)

        hel_list = []
        for node in health_list:
            host = node.get('host', None)
            node_id = node.get('id', None)
            pre_status = node.get('pre_status', None)
            thd = utils.MultiThread(_thread_func_for_other,
                                    host, node_id, pre_status)
            hel_list.append(thd)

        utils.start_threads(nav_list)
        utils.start_threads(hel_list)

        """
        Ignore mds migration
        if is_mds:
            # delete mds on this server.
            values = {'mds': 'no'}
            db.init_node_update(context, node_id, values)
            self.ceph_driver.remove_mds(context, node_id)
            # Find a new node, start mds on that node.
            nodes = db.init_node_get_all(context)
            active_list = []
            for ser in nodes:
                if ser['status'] == 'Active':
                    active_list.append(ser)
            active_host = random.choice(active_list)
            self._agent_rpcapi.add_mds(context, active_host['host'])
        """

    @periodic_task(spacing=FLAGS.update_time_interval)
    def update_node_datetime(self, context):
        """Update the update-at of each node in db with current time."""
        values = {'updated_at': timeutils.utcnow()}
        hostname, err = utils.execute('hostname')
        if not err:
            node = db.init_node_get_by_host(context, hostname.strip())
            if node is not None:
                db.init_node_update(context, node['id'], values)
        else:
            try:
                raise exception.ExeCmdError
            except exception.ExeCmdError, e:
                LOG.error("%s:%s" % (e.code, e.message))

    @periodic_task(service_topic=FLAGS.agent_topic, spacing=_get_interval_time('ceph_status'))
    def update_ceph_status(self, context):
        all_pool = db.pool_get_all(context)
        if len(all_pool) < 1:
            return 'NotCreateCluster'

        def __get_ceph_status():
            args = ['ceph', 'status', '--connect-timeout', '10']
            return self.ceph_driver._run_cmd_to_json(args)
        def _ceph_status():
            is_active = True
            try:
                sum_dict = __get_ceph_status()
                ceph_status = sum_dict['health']['overall_status']
                ceph_status = {'is_ceph_active': is_active,
                               'health_list': [ceph_status, ceph_status]}
                return json.dumps(ceph_status), is_active
            except exception.ProcessExecutionError as e:
                if e.exit_code == 1 and e.stderr.find('InterruptedOrTimeoutError') != -1:
                    is_active = False
                    LOG.debug('Update ceph status. Set active to false')
                ceph_status = {'is_ceph_active': is_active,
                               'health_list': ['CRITICAL_ERROR', 'ERROR'],
                               'health': 'CRITICAL_ERROR'}
                return json.dumps(ceph_status), is_active

        while not self._cluster_id:
            time.sleep(10)

        cluster_id = self._cluster_id
        sum_dict, is_active = _ceph_status()
        val = {'summary_data': sum_dict}

        # set montior summary status.
        if not is_active:
            db.summary_update(context, cluster_id, 'cluster', val)
            db.summary_update(context, cluster_id, 'ceph', val)
            db.summary_update(context, cluster_id, 'mon', val)
        else:
            # If ceph is running, update summary info by old_method.
            thd = utils.MultiThread(self.update_summary, context=context)
            thd.start()

        if not is_active:
            return 'CRITICAL_ERROR'
        else:
            return 'HEALTH_OK'

    def health_status(self, context):
        return self.update_ceph_status(context)

    def inital_ceph_osd_db_conf(self, context, server_list):
        """Begin to reate ceph.conf and initial ceph osd in ceph."""
        cluster_ref = db.cluster_get(context, self._cluster_id)
        file_system = cluster_ref['file_system']
        return self.ceph_driver.inital_ceph_osd_db_conf(context,
                                                        server_list,
                                                        file_system)

    def add_cache_tier(self, context, body):
        return self.ceph_driver.add_cache_tier(context, body)

    def remove_cache_tier(self, context, body):
        return self.ceph_driver.remove_cache_tier(context, body)
