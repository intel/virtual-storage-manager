# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at:
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# pylint: disable=R0914
# pylint: disable=R0913

"""
Drivers for testdbs.

"""

import os
import time
import json
from vsm import db
from vsm import exception
from vsm import flags
from vsm.openstack.common import log as logging
from vsm import utils
from vsm.openstack.common.gettextutils import _
from vsm import conductor
from vsm.conductor import rpcapi as conductor_rpcapi
from vsm.agent import rpcapi as agent_rpc
from vsm.agent import cephconfigparser
from vsm.openstack.common.rpc import common as rpc_exc

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class CephDriver(object):
    """Excute commands relating to Ceph."""
    def __init__(self):
        self._crushmap_mgmt = CreateCrushMapDriver()
        self._conductor_api = conductor.API()
        self._conductor_rpcapi = conductor_rpcapi.ConductorAPI()
        self._agent_rpcapi = agent_rpc.AgentAPI()
        try:
            cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        except:
            pass

    def _get_new_ruleset(self):
        args = ['ceph', 'osd', 'crush', 'rule', 'dump']
        ruleset_list = self._run_cmd_to_json(args)
        return len(ruleset_list)

    def create_storage_pool(self, context, body):
        pool_name = body["name"]
        primary_storage_group = replica_storage_group = ""
        if body.get("ec_profile_id"):
            profile_ref = db.ec_profile_get(context, body['ec_profile_id'])
            pgp_num = pg_num = profile_ref['pg_num'] 
            plugin = "plugin=" + profile_ref['plugin']
            ruleset_root = "ruleset-root=" + body['ec_ruleset_root']
            failure_domain = "ruleset-failure-domain=" + body['ec_failure_domain']
            rule_name = pool_name

            kv = eval(profile_ref['plugin_kv_pair'])
            pair_str = ""
            for k, v in kv.items():
               pair_str += str(k) + "=" + str(v) + " " 
    
            utils.execute('ceph', 'osd', 'erasure-code-profile','set', profile_ref['name'], \
                            plugin, ruleset_root, failure_domain, pair_str, '--force', \
                            run_as_root=True)

            utils.execute('ceph', 'osd', 'crush', 'rule', 'create-erasure', \
                            rule_name, profile_ref['name'], run_as_root=True)

            res = utils.execute('ceph', 'osd', 'pool', 'create', pool_name, pg_num, \
                            pgp_num, 'erasure', profile_ref['name'], rule_name, \
                            run_as_root=True) 
        elif body.get('replica_storage_group_id'):
            try:
                utils.execute('ceph', 'osd', 'getcrushmap', '-o', FLAGS.crushmap_bin,
                                run_as_root=True)
                utils.execute('crushtool', '-d', FLAGS.crushmap_bin, '-o', FLAGS.crushmap_src, 
                                run_as_root=True)
                ruleset = self._get_new_ruleset()
                storage_group_list = db.storage_group_get_all(context)
                storage_group_id = int(body['storage_group_id'])
                replica_storage_group_id = int(body['replica_storage_group_id'])
                pg_num = str(body['pg_num'])
                for x in storage_group_list:
                    if x['id'] == storage_group_id and \
                        x['id'] == replica_storage_group_id:
                        primary_storage_group = replica_storage_group = x['name']
                    elif x['id'] == storage_group_id:
                        primary_storage_group = x['name']
                    elif x['id'] == replica_storage_group_id:
                        replica_storage_group = x['name']
                    else:
                        continue
                if not (primary_storage_group and replica_storage_group):        
                    LOG.error("Can't find primary_storage_group_id or replica_storage_group_id")
                    raise 
                    return False

                type = "host" 
                #TODO min_size and max_size
                rule_str = "rule " + pool_name + "_replica {"
                rule_str += "    ruleset " + str(ruleset)
                rule_str += "    type replicated" 
                rule_str += "    min_size 0"
                rule_str += "    max_size 10"
                rule_str += "    step take " + primary_storage_group
                rule_str += "    step chooseleaf firstn 1 type " + type
                rule_str += "    step emit"
                rule_str += "    step take " + replica_storage_group
                rule_str += "    step chooseleaf firstn " + str(body['size'] - 1) + " type " + type
                rule_str += "    step emit"
                rule_str += "}"

                utils.execute('chown', '-R', 'vsm:vsm', '/etc/vsm/',
                        run_as_root=True) 
                if utils.append_to_file(FLAGS.crushmap_src, rule_str):
                    utils.execute('crushtool', '-c', FLAGS.crushmap_src, '-o', FLAGS.crushmap_bin, \
                                    run_as_root=True) 
                    utils.execute('ceph', 'osd', 'setcrushmap', '-i', FLAGS.crushmap_bin, \
                                    run_as_root=True)
                    utils.execute('ceph', 'osd', 'pool', 'create', pool_name, \
                                pg_num, pg_num, 'replicated', run_as_root=True)
                    utils.execute('ceph', 'osd', 'pool', 'set', pool_name,
                                'crush_ruleset', ruleset, run_as_root=True)
                    utils.execute('ceph', 'osd', 'pool', 'set', pool_name,
                                'size', str(body['size']), run_as_root=True)
                    res = True
                else:
                    LOG.error("Failed while writing crushmap!")
                    return False 
            except:
                LOG.error("create replica storage pool error!")
                raise
                return False  
        else:
            rule = str(body['crush_ruleset'])
            size = str(body['size'])
            pg_num = str(body['pg_num'])
            res = utils.execute('ceph', 'osd', 'pool', 'create', pool_name, \
                                pg_num, run_as_root=True)
            utils.execute('ceph', 'osd', 'pool', 'set', pool_name,
                            'size', size, run_as_root=True)
            utils.execute('ceph', 'osd', 'pool', 'set', pool_name,
                            'crush_ruleset', rule, run_as_root=True)
        #set quota
        if body.get('enable_quota', False):
            max_bytes = 1024 * 1024 * 1024 * int(body.get('quota', 0))
            utils.execute('ceph', 'osd', 'pool', 'set-quota', pool_name, 'max_bytes', max_bytes,\
                            run_as_root=True)  
        #update db
        pool_list = self.get_pool_status()
        for pool in pool_list:
            if pool_name == pool['pool_name']:
                values = {
                    'pool_id': pool.get('pool'),
                    'name': pool.get('pool_name'),
                    'pg_num': pool.get('pg_num'),
                    'pgp_num': pool.get('pg_placement_num'),
                    'size': pool.get('size'),
                    'min_size': pool.get('min_size'),
                    'crush_ruleset': pool.get('crush_ruleset'),
                    'crash_replay_interval': pool.get('crash_replay_interval'),
                    'ec_status': pool.get('erasure_code_profile'),
                    'replica_storage_group': replica_storage_group if replica_storage_group else None, 
                    'quota': body.get('quota')
                }
                values['created_by'] = body.get('created_by')
                values['cluster_id'] = body.get('cluster_id')
                values['tag'] = body.get('tag')
                values['status'] = 'running'
                values['primary_storage_group_id'] = body.get('storage_group_id')
                db.pool_create(context, values)

        return res

    def present_storage_pools(self, context, info):
        LOG.info(' agent present_storage_pools()')
        LOG.info(' body = %s' % info)

        vsmapp_ip = info['vsmapp_ip']
        pool_infos = info['pool_infos']

        pools_str = ""
        for pinfo in pool_infos:
            pool_type = pinfo['type'] + "-" + pinfo['name']
            # We use "vsm-" key words to delete unused pools to openstack.
            temp_str = pinfo['name'] + "," + pool_type
            pools_str = pools_str + " " + temp_str

        LOG.info('pools_str = %s' % pools_str)
        out, err = utils.execute('presentpool',
                                 vsmapp_ip,
                                 pools_str,
                                 run_as_root=True)
        LOG.info('running logs = %s' % out)
        return out, err

    def _create_osd_state(self, context, strg, osd_id):
        osd_state = {}
        osd_state['osd_name'] = 'osd.%d' % osd_id
        osd_state['device_id'] = strg['dev_id']
        osd_state['storage_group_id'] = strg['storage_group_id']
        osd_state['service_id'] = strg['service_id']
        osd_state['cluster_id'] = strg['cluster_id']
        osd_state['state'] = FLAGS.osd_in_up
        osd_state['operation_status'] = FLAGS.vsm_status_present
        osd_state['weight'] = 1.0
        osd_state['public_ip'] = strg['secondary_public_ip']
        osd_state['cluster_ip'] = strg['cluster_ip']
        osd_state['deleted'] = 0
        osd_state['weight'] = 1.0
        osd_state['operation_status'] = FLAGS.vsm_status_present
        osd_state['zone_id'] = strg['zone_id']
        LOG.info('ADD_OSD _create_osd_state %s' % osd_state)
        self._conductor_rpcapi.osd_state_create(context, osd_state)

    def _remove_osd_state(self, context, id):
        osd_name = 'osd.%s' % id
        val = { 'osd_name': osd_name, 'deleted': 1 }
        self._conductor_rpcapi.osd_state_update_or_create(context,
            val, create=False)

    def get_ceph_config(self, context):
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf).as_dict()
        LOG.info("ceph config %s" % config)
        return config

    def save_ceph_config(self, context, config):
        """
        config: dict
        """
        config = cephconfigparser.CephConfigParser(config)
        #with open(FLAGS.ceph_conf, 'w') as ceph_conf:
        config.save_conf(FLAGS.ceph_conf)
        return True

    def inital_ceph_osd_db_conf(self, context, server_list, file_system):
        config = cephconfigparser.CephConfigParser()
        osd_num = db.device_get_count(context)
        LOG.info("osd_num:%d" % osd_num)
        pg_count_factor = 200
        settings = db.vsm_settings_get_all(context)
        for setting in settings:
            if setting['name'] == 'ceph_near_full_threshold':
                cnfth = setting['value']
            elif setting['name'] == 'ceph_full_threshold':
                cfth = setting['value']
            elif setting['name'] == 'pg_count_factor':
                pg_count_factor = int(setting['value'])
            elif setting['name'] == 'heartbeat_interval':
                heartbeat_interval = setting['value']
            elif setting['name'] == 'osd_heartbeat_interval':
                osd_heartbeat_interval = setting['value']
            elif setting['name'] == 'osd_heartbeat_grace':
                osd_heartbeat_grace = setting['value']
            

        pg_num = osd_num * pg_count_factor / 2
        config.add_global(pg_num=pg_num, \
                          cnfth=cnfth, \
                          cfth=cfth,
                          heartbeat_interval=heartbeat_interval,
                          osd_heartbeat_interval=osd_heartbeat_interval,
                          osd_heartbeat_grace=osd_heartbeat_grace)

        is_first_mon = True
        is_first_osd = True
        mon_cnt = -1
        osd_cnt = -1

        for host in server_list:
            #DEBUG for debug here.
            LOG.info(' host list: %s' % host)
            if host['is_monitor']:
                mon_cnt = mon_cnt + 1
                monitor = db.init_node_get_by_id(context, host['id'])
                hostname = monitor['host']
                hostip = monitor['secondary_public_ip']
                if is_first_mon:
                    config.add_mds_header()
                    #config.add_mds(hostname, hostip, '0')
                    #values = {'mds': 'yes'}
                    #db.init_node_update(context, host['id'], values)
                    config.add_mon_header()
                    is_first_mon = False
                    config.add_mon(hostname, hostip, mon_cnt)
                else:
                    config.add_mon(hostname, hostip, mon_cnt)

            if host['is_storage']:
                # Get disks list info from DB.
                strgs = self._conductor_rpcapi.\
                    host_storage_groups_devices(context,
                                                host['id'])

                LOG.info('strg list: %s' % strgs)
                if strgs and is_first_osd:
                    fs_type = strgs[0]['file_system']
                    # validate fs type
                    if fs_type in ['xfs', 'ext3', 'ext4', 'btrfs']:
                        config.add_osd_header(osd_type=fs_type)
                    else:
                        config.add_osd_header()
                    is_first_osd = False
                for strg in strgs:
                    # NOTE: osd_cnt stands for the osd_id.
                    osd_cnt = osd_cnt + 1
                    LOG.info(' strg = %s' % \
                            (json.dumps(strg, sort_keys=True, indent=4)))

                    config.add_osd(strg['host'],
                                   (strg['secondary_public_ip'],
                                    strg['primary_public_ip']),
                                   strg['cluster_ip'],
                                   strg['dev_name'],
                                   strg['dev_journal'],
                                   osd_cnt)

                    self._create_osd_state(context,
                                           strg,
                                           osd_cnt)
                    mount_point = '%sosd%s' % \
                        (FLAGS.osd_data_path, osd_cnt)
                    utils.ensure_tree(mount_point)

                    val = {}
                    val['id'] = strg['dev_id']
                    val['mount_point'] = mount_point
                    val['fs_type'] = file_system
                    LOG.info('device_update values = %s, osd_id = %s' % \
                         (val, osd_cnt))
                    self._conductor_api.device_update(context, val['id'], val)

        config.save_conf(FLAGS.ceph_conf)

    def mkcephfs(self):
        LOG.info('mkcephfs in agent/driver.py')
        utils.execute('mkcephfs',
                      '-a',
                      '-c', FLAGS.ceph_conf,
                      '-k', FLAGS.keyring_admin,
                      # '--mkfs',
                      run_as_root=True)
        LOG.info('mkcephfs over in agent/driver.py')
        return True

    def start_ceph(self, context):
        utils.execute('service', 'ceph', '-a', 'start', run_as_root=True)
        return True

    def _stop_all_ceph_service(self):
        run_path = '/var/run/ceph/'
        try:
            pids = utils.execute('ls', run_path, run_as_root=True)[0]
            for pid_file in pids.split():
                try:
                    LOG.info('KILL %s' % pid_file)
                    if pid_file.find('pid') != -1:
                        self._kill_by_pid_file(run_path + pid_file)
                except:
                    LOG.info('KILL PROCESS')

            pids = utils.execute('pgrep', 'ceph', run_as_root=True)[0]
            for pid in pids.split():
                try:
                    LOG.info('KILL pid = %s' % pid)
                    utils.execute('kill', '-9',
                                  pid,
                                  ignore_exit_code=True,
                                  run_as_root=True)
                except:
                    LOG.info('KILL BY PGREP')
        except:
            LOG.info('Stop meet error')

    def _clean_dirs(self, dir_path):
        try:
            files = utils.execute('ls', dir_path, run_as_root=True)[0]
            files = files.split()
            for f in files:
                try:
                    utils.execute('rm', '-rf', dir_path + "/" + f,
                                        ignore_exit_code=True,
                                        run_as_root=True)
                except:
                    LOG.info('Error when delete file = %s' % f)
        except:
            LOG.info('LOOK UP dir failed %s' % dir_path)

    def _clean_ceph_conf(self):
        try:
            self._clean_dirs('/etc/ceph/')
        except:
            LOG.info('Delete files meet error!')

    def _clean_lib_ceph_files(self):
        # delete dirty files in mds.
        try:
            osd_list = utils.execute('ls', '/var/lib/ceph/osd/',
                                     ignore_exit_code=True,
                                     run_as_root=True)[0]
            LOG.info('Get osd_list = %s' % osd_list)
            for osd in osd_list.split():
                try:
                    LOG.info('Begin to umount %s' % osd)
                    self._clean_dirs('/var/lib/ceph/osd/%s' % osd)
                    utils.execute('umount', '/var/lib/ceph/osd/' + osd,
                                  ignore_exit_code = True,
                                  run_as_root=True)
                except:
                    LOG.info('umount /var/lib/ceph/osd/%s' % osd)
            self._clean_dirs('/var/lib/ceph/')
        except:
            LOG.info('rm  monitor files error')

    def _build_lib_ceph_dirs(self):
        try:
            dirs_list = ['bootstrap-mds', 'bootstrap-osd',
                         'mds', 'mon', 'osd', 'tmp']
            for d in dirs_list:
                utils.execute('mkdir', '-p', '/var/lib/ceph/' + d,
                              run_as_root=True)
        except:
            LOG.info('build dirs in /var/lib/ceph failed!')

    def __format_devs(self, disks, file_system):
        # format devices to xfs.
        def ___fdisk(disk):
            mkfs_option = utils.get_fs_options(file_system)[0]
            utils.execute('mkfs.%s' % file_system,
                          mkfs_option,
                          disk,
                          run_as_root=True)

        thd_list = []
        for disk in disks:
            thd = utils.MultiThread(___fdisk, disk=disk)
            thd_list.append(thd)

        try:
            utils.start_threads(thd_list)
        except:
            pass

    def clean_ceph_data(self, context, osd_disks, journal_disks, file_system):
        utils.execute('chown', '-R', 'vsm:vsm', '/var/lib/ceph/',
                        run_as_root=True)
        self._stop_all_ceph_service()
        self._stop_all_ceph_service()
        time.sleep(1)
        self._clean_ceph_conf()
        self._clean_lib_ceph_files()
        self._build_lib_ceph_dirs()
        self.__format_devs(osd_disks + journal_disks, file_system)
        return {'status': 'ok'}

    def mount_disks(self, devices, fs_type):
        def __mount_disk(disk):
            utils.execute('mkdir',
                          '-p',
                          disk['mount_point'],
                          run_as_root=True)
            mount_options = utils.get_fs_options(fs_type)[1]
            utils.execute('mount',
                          '-t', fs_type,
                          '-o', mount_options,
                          disk['name'],
                          disk['mount_point'],
                          run_as_root=True)

        thd_list = []
        for dev in devices:
            thd = utils.MultiThread(__mount_disk, disk=dev)
            thd_list.append(thd)
        utils.start_threads(thd_list)

    def is_new_storage_group(self, storage_group):
        nodes = self.get_crushmap_nodes()
        for node in nodes:
            if storage_group == node['name']:
                return False
        return True

    def add_osd(self, context, host_id):
        LOG.info('start to ceph osd on %s' % host_id)
        strg_list = self._conductor_api.\
            host_storage_groups_devices(context, host_id)
        LOG.info('strg_list %s' % strg_list)

        #added_to_crushmap = False
        for strg in strg_list:
            LOG.info('>> Step 1: start to ceph osd %s' % strg)
            # Create osd from # ceph osd create
            stdout = utils.execute("ceph",
                                   "osd",
                                   "create",
                                   run_as_root=True)[0]

            osd_id = str(int(stdout))
            LOG.info('   gen osd_id success: %s' % osd_id)

            # step 1 end
            host = strg['host']
            zone = strg['zone']

            #TODO strg['storage_group']
            # stands for the storage_group_name fetch from DB.
            storage_group = strg['storage_group']
            crush_dict = {"root": "vsm",
                          "storage_group": storage_group,
                          "zone": "_".join([zone, storage_group]),
                          "host": "_".join([host, storage_group, zone]),}

            osd_conf_dict = {"host": host,
                             "primary_public_ip": strg['primary_public_ip'],
                             "secondary_public_ip": strg['secondary_public_ip'],
                             "cluster_ip": strg['cluster_ip'],
                             "dev_name": strg['dev_name'],
                             "dev_journal": strg['dev_journal'],
                             "file_system": strg['file_system']}
            osd_state = {}
            osd_state['osd_name'] = 'osd.%s' % osd_id
            osd_state['device_id'] = strg['dev_id']
            osd_state['storage_group_id'] = strg['storage_group_id']
            osd_state['service_id'] = strg['service_id']
            osd_state['cluster_id'] = strg['cluster_id']
            osd_state['state'] = FLAGS.osd_in_up
            osd_state['weight'] = 1.0
            osd_state['operation_status'] = FLAGS.vsm_status_present
            osd_state['public_ip'] = strg['secondary_public_ip']
            osd_state['cluster_ip'] = strg['cluster_ip']
            osd_state['deleted'] = 0
            osd_state['zone_id'] = strg['zone_id']

            LOG.info('>> crush_dict  %s' % crush_dict)
            LOG.info('>> osd_conf_dict %s' % osd_conf_dict)
            LOG.info('>> osd_state %s' % osd_state)
            values = {}
            #if not added_to_crushmap:
            #    LOG.info('>> add crushmap ')
            if self.is_new_storage_group(crush_dict['storage_group']):
                self._crushmap_mgmt.add_storage_group(crush_dict['storage_group'],\
                                                  crush_dict['root'])
                zones = db.zone_get_all(context)
                for item in zones: 
                    zone_item = item['name'] + '_' + crush_dict['storage_group'] 
                    self._crushmap_mgmt.add_zone(zone_item, \
                                                crush_dict['storage_group'])
                
                if zone == FLAGS.default_zone:
                    self._crushmap_mgmt.add_rule(crush_dict['storage_group'], 'host') 
                else:
                    self._crushmap_mgmt.add_rule(crush_dict['storage_group'], 'zone')

                #TODO update rule_id and status in DB
                rule_dict = self.get_crush_rule_dump_by_name(crush_dict['storage_group']) 
                LOG.info("rule_dict:%s" % rule_dict)
                values['rule_id'] = rule_dict['rule_id'] 

            self._crushmap_mgmt.add_host(crush_dict['host'],
                                         crush_dict['zone'])
            #    added_to_crushmap = True

            #There must be at least 3 hosts in every storage group when the status is "IN"
            zones, hosts = self._conductor_rpcapi.zones_hosts_get_by_storage_group(context, \
                                                        crush_dict['storage_group'])
            #LOG.info("storage group:%s" % crush_dict['storage_group'])
            #LOG.info("zones:%s" % zones)
            #LOG.info("hosts:%s" % hosts)
            #no zone and zone version
            if zones:
                if zones[0] == FLAGS.default_zone:
                    if host not in hosts and len(hosts) >= 2:
                        values['status'] = FLAGS.storage_group_in 
                else:
                    if zone not in zones and len(zones) >= 2:
                        values['status'] = FLAGS.storage_group_in 

            if values:
                db.storage_group_update_by_name(context, crush_dict['storage_group'], values)

            # other steps
            LOG.info('>> _add_osd start ')
            self._add_osd(context,
                          osd_id,
                          crush_dict,
                          osd_conf_dict,
                          osd_state)
        return True

    def _add_osd(self,
                 context,
                 osd_id,
                 crush_dict,
                 osd_conf_dict,
                 osd_state,
                 weight="1.0"):

        # step 2
        LOG.info('>>> step2 start')
        #osd_pth = '%sceph-%s' % (FLAGS.osd_data_path, osd_id)
        #osd_keyring_pth = "%s/keyring" % osd_pth
        osd_pth = '/var/lib/ceph/osd/osd%s' % osd_id
        osd_keyring_pth = '/etc/ceph/keyring.osd.%s' % osd_id
        utils.ensure_tree(osd_pth)

        # step 3
        LOG.info('>>> step3 start')
        # get cluster file system to format the disk
        utils.execute("umount",
                      osd_conf_dict['dev_name'],
                      check_exit_code=False,
                      run_as_root=True)

        LOG.debug("The file system is %s" % osd_conf_dict['file_system'])
        file_system = 'xfs'
        if osd_conf_dict['file_system']:
            file_system = osd_conf_dict['file_system']

        mkfs_option = utils.get_fs_options(file_system)[0]
        utils.execute("mkfs",
                      "-t", file_system,
                      mkfs_option, osd_conf_dict['dev_name'],
                      run_as_root=True)

        # TODO: does not support ext4 for now.
        # Need to use -o user_xattr for ext4
        fs_opt = utils.get_fs_options(file_system)[1]
        utils.execute("mount",
                      "-t", file_system,
                      "-o", fs_opt,
                      osd_conf_dict['dev_name'],
                      osd_pth,
                      run_as_root=True)
        self._clean_dirs(osd_pth)

        # step 3.1
        LOG.info('>>> step3.1 start')
        ret = self._add_ceph_osd_to_config(context, osd_conf_dict, osd_id)

        # step 4 add to config file before this step
        LOG.info('>>> step4 start')
        utils.execute("ceph-osd", "-i", osd_id, "--mkfs", "--mkkey",
                       run_as_root=True)

        # step 5
        LOG.info('>>> step5 start')
        utils.execute("ceph", "auth", "del", "osd.%s" % osd_id,
                        run_as_root=True)
        utils.execute("ceph", "auth", "add", "osd.%s" % osd_id,
                      "osd", "allow *", "mon", "allow rwx",
                      "-i", osd_keyring_pth,
                      run_as_root=True)

        # step 6 zone host stg
        LOG.info('>>> step6 start')
        utils.execute("ceph", "osd", "crush", "add", "osd.%s" % osd_id, weight,
                 "root=%s" % crush_dict['root'],
                 "storage_group=%s" % crush_dict['storage_group'],
                 "zone=%s" % crush_dict['zone'], "host=%s" % crush_dict['host'],
                 run_as_root=True)

        # step 7 start osd service
        LOG.info('>>> step7 start')
        self.start_osd_daemon(context, osd_id)

        self._conductor_api.osd_state_create(context, osd_state)
        LOG.info('>>> step7 finish')
        return True

    def _add_ceph_osd_to_config(self, context, strg, osd_id):
        LOG.info('>>>> _add_ceph_osd_to_config start')
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        ip = (strg['secondary_public_ip'], strg['primary_public_ip'])

        config.add_osd(strg['host'], ip, strg['cluster_ip'],
                strg['dev_name'], strg['dev_journal'], osd_id)

        LOG.info('>>>> _add_ceph_osd_to_config config %s ' % config.as_dict())
        LOG.info('>>>> _add_ceph_osd_to_config added')
        config.save_conf(FLAGS.ceph_conf)
        return True

    def add_monitor(self, context, host_id, mon_id, port="6789"):
        LOG.info('>> start to add mon %s on %s' % (mon_id, host_id))
        ser = self._conductor_rpcapi.init_node_get_by_id(context, host_id)
        host_ip = ser['secondary_public_ip']
        LOG.info('>> start to add mon %s' % host_ip)
        # TODO
        # step 1
        LOG.info('>> add mon step 1 ')
        utils.ensure_tree(os.path.join(FLAGS.monitor_data_path,
            "mon" + mon_id))
        # step 2
        LOG.info('>> add mon step 2 ')
        tmp_pth = "/tmp"
        monitor_key_pth = os.path.join(tmp_pth, 'monitor_key')
        monitor_map_pth = os.path.join(tmp_pth, 'monitor_map')
        # step 3
        LOG.info('>> add mon step 3 ')
        utils.execute("ceph", "auth", "get", "mon.", "-o", monitor_key_pth,
                        run_as_root=True)
        # step 4
        LOG.info('>> add mon step 4 ')
        utils.execute("ceph", "mon", "getmap", "-o", monitor_map_pth,
                        run_as_root=True)
        # step 5
        LOG.info('>> add mon step 5 ')
        utils.execute("ceph-mon", "-i", mon_id, "--mkfs",
            "--monmap", monitor_map_pth,
            "--keyring", monitor_key_pth,
            run_as_root=True)
        ## step 6
        #LOG.info('>> add mon step 6 ')
        #host = ":".join([host_ip, port])
        #utils.execute("ceph", "mon", "add", mon_id, host, run_as_root=True)
        ## step 7
        #LOG.info('>> add mon step 7 ')
        #self._add_ceph_mon_to_config(context, ser['host'], host_ip, mon_id=mon_id)
        #utils.execute("ceph-mon", "-i", mon_id, "--public-addr", host,
        #                run_as_root=True)

        #changed by ly
        # step 6
        LOG.info('>> add mon step 6 ')
        host = ":".join([host_ip, port])
        self._add_ceph_mon_to_config(context, ser['host'], host_ip, mon_id=mon_id)
        #utils.execute("ceph-mon", "-i", mon_id, "--public-addr", host,
        #                run_as_root=True)
        self.start_mon_daemon(context, mon_id)
        # step 7
        LOG.info('>> add mon step 7 ')
        utils.execute("ceph", "mon", "add", mon_id, host, run_as_root=True)
        LOG.info('>> add mon finish %s' % mon_id)
        return True

    def remove_monitor(self, context, host_id, is_stop=False):
        LOG.info('>> start to remove ceph mon on : %s' % host_id)
        # get host_name
        node = self._conductor_rpcapi.init_node_get_by_id(context, host_id)
        host = node['host']

        # get config
        LOG.info('>> removeing ceph mon')
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config_dict = config.as_dict()

        # get mon_id
        mon_id = None
        for section in config_dict:
            if section.startswith("mon."):
                if config_dict[section]['host'] == host:
                    mon_id = section.replace("mon.", "")
        if not mon_id:
            LOG.info('>> removeing ceph mon not found')
            return True

        # step 1
        LOG.info('>> removeing ceph mon %s' % mon_id)
        LOG.info('>> removeing ceph mon step 1')
        try:
            # test ssh service in case the server is down
            utils.execute('ssh', '-q', 'root@' + host, 'exit', run_as_root=True)
        except exception.ProcessExecutionError as e:
            code = e.exit_code
            LOG.info('return code: %s' % code)
            if code == 0:
                utils.execute("service",
                              "ceph",
                              "-a",
                              "stop",
                              "mon.%s" % mon_id,
                              run_as_root=True)
            # If can not ssh to that server,
            # We assume that the server has been shutdown.
            # Go steps below.

        # step 2
        LOG.info('>> removeing ceph mon step 2')
        utils.execute("ceph",
                      "mon",
                      "remove",
                      mon_id,
                      run_as_root=True)
        if not is_stop:
            config.remove_mon(mon_id)
        # step 3
        LOG.info('>> removeing ceph mon step 3')

        config.save_conf(FLAGS.ceph_conf)
        return True

        # TODO  don't remove any code from this line to the end of func
        # remove monitors from unhealthy cluster
        # step 1
        try:
            utils.execute("service", "ceph", "stop", "mon", run_as_root=True)
        except:
            utils.execute("stop", "ceph-mon-all", run_as_root=True)
        # step 2
        LOG.info('>> remove ceph mon step2 start')
        tmp_pth = "/tmp"
        monitor_map_pth = os.path.join(tmp_pth, 'monitor_map')
        utils.execute("ceph-mon", "-i", mon_id, "--extract-monmap",
                        monitor_map_pth, run_as_root=True)
        utils.execute("ceph-mon", "-i", "a", "--extract-monmap",
                        monitor_map_pth, run_as_root=True)
        # step 3
        LOG.info('>> remove ceph mon step3 start')
        utils.execute("monmaptool", monitor_map_pth, "--rm", mon_id,
                        run_as_root=True)
        # step 4
        LOG.info('>> remove ceph mon step4 start')
        utils.execute("ceph-mon", "-i", mon_id, "--inject-monmap",
                        monitor_map_pth, run_as_root=True)
        return True

    def remove_mds(self, context, host_id):
        """Remove mds service on host_id server."""
        def __is_host_running(host):
            try:
                self._agent_rpcapi.test_service(context,
                                                FLAGS.agent_topic,
                                                host)
                return True
            except rpc_exc.Timeout, rpc_exc.RemoteError:
                return False

        def __config_dict():
            config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
            cdict = config.as_dict()
            return cdict

        def __config_remove_mds(mds_id):
            config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
            config.remove_mds_header()
            config.remove_mds(mds_id)
            config.save_conf(FLAGS.ceph_conf)

        LOG.info('>> remove ceph mds on hostid(%s) start' % host_id)
        node = self._conductor_rpcapi.init_node_get_by_id(context, host_id)
        values = {'mds': 'no'}
        self._conductor_rpcapi.init_node_update(context, host_id, values)
        host = node['host']
        host_is_running = __is_host_running(host)
        if host_is_running:
            try:
                self._agent_rpcapi.stop_mds(context, host)
            except rpc_exc.Timeout, rpc_exc.RemoteError:
                host_is_running = False
        mds_id = self.get_mds_id(host)
        if not mds_id:
            LOG.info('Have not find mds on %s' % host_id)
            return

        __config_remove_mds(mds_id)
        utils.execute('ceph', 'mds',
                      'rm', mds_id, 'mds.%s' % mds_id,
                      run_as_root=True)
        utils.execute('ceph', 'auth', 'del',
                      'mds.%s' % mds_id,
                      run_as_root=True)
        utils.execute('ceph', 'mds', 'newfs', '0', '1',
                      '--yes-i-really-mean-it',
                      run_as_root=True)
        LOG.info('remove mds success!')

    def remove_osd(self, context, host_id):
        def __is_host_running(host):
            try:
                self._agent_rpcapi.test_service(context,
                                                FLAGS.agent_topic,
                                                host)
                return True
            except rpc_exc.Timeout, rpc_exc.RemoteError:
                return False

        def __config_dict():
            config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
            cdict = config.as_dict()
            return cdict

        def __config_remove_osd(osd_id):
            config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
            config.remove_osd(osd_id)
            config.save_conf(FLAGS.ceph_conf)

        LOG.info('>> remove ceph osds on hostid(%s) start' % host_id)
        node = self._conductor_rpcapi.init_node_get_by_id(context, host_id)
        host = node['host']
        host_is_running = __is_host_running(host)

        # get config
        config_dict = __config_dict()

        # get osd_ids
        osd_id_list = []
        for section in config_dict:
            if section.startswith("osd."):
                if config_dict[section]['host'] == host:
                    osd_id_list.append(section.replace("osd.", ""))
        LOG.info('>> remove ceph osd osd_ids %s' % osd_id_list)

        for osd_id in osd_id_list:
            self._remove_osd(context, osd_id, host_is_running)
            # step 5
            LOG.info('>>> remove ceph osd step5 osd_id %s' % osd_id)
            osd_name = 'osd.%s' % osd_id
            val = { 'osd_name': osd_name, 'deleted': 1 }
            self._conductor_rpcapi.osd_state_update(context, val)
            LOG.info('>>> remove ceph osd step 1-5 osd_id %s' % osd_id)

        #step 6
        LOG.info('>>> Begin to remove crushmap')
        osd_tree = utils.execute('ceph', 'osd', 'tree', run_as_root=True)[0]
        LOG.info('>>> Get ceph osd tree = %s' % osd_tree)
        for line in osd_tree.split('\n'):
            if line.lower().find(host.lower()) != -1:
                for x in line.split(' '):
                    if x.lower().find(host.lower()) != -1:
                        utils.execute('ceph', 'osd', 'crush', 'rm', x)

        LOG.info('>>> remove ceph osd finish.')

        if not host_is_running:
            val = {'deleted': 1}
            self._conductor_rpcapi.init_node_update(context, host_id, val)
        return True

    def _add_ceph_mon_to_config(self, context, host, host_ip, mon_id):
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config.add_mon(host, host_ip, mon_id=mon_id)
        config.save_conf(FLAGS.ceph_conf)
        return True

    def _kill_by_pid_file(self, pid_file):
        # Kill process by pid file.
        # mainly for ceph.
        file_path = pid_file
        if os.path.exists(file_path):
            pid = open(file_path).read().strip()
            pid_live = os.path.exists('/proc/%s' % pid)
            utils.execute('rm', '-rf', file_path, run_as_root=True)
            try_times = 1
            while pid_live:
                try_times = try_times + 1

                try:
                    if try_times % 2:
                        utils.execute('kill', '-9', pid, run_as_root=True)
                    else:
                        utils.execute('kill', '-9', pid, run_as_root=True)
                except:
                    LOG.info('Seems can not stop this OSD process.')
                time.sleep(2)
                pid_live = os.path.exists('/proc/%s' % pid)
                if try_times > 100:
                    break
        return True

    def stop_osd_daemon(self, context, num):
        # stop ceph-osd daemon on the storage node
        # Param: the osd id
        # return Bool
        file_path = '/var/run/ceph/osd.%s.pid' % num
        if os.path.exists(file_path):
            self._kill_by_pid_file(file_path)
        else:
            LOG.info('Can not find pid file for osd.%s' % num)
        return True

    def start_osd_daemon(self, context, num):
        osd = "osd.%s" % num
        LOG.info('begin to start osd = %s' % osd)
        utils.execute('service', 'ceph', 'start', osd, run_as_root=True)
        return True

    def stop_mon_daemon(self, context, num):
        file_path = '/var/run/ceph/mon.%s.pid' % num
        if os.path.exists(file_path):
            self._kill_by_pid_file(file_path)
        else:
            LOG.info('Can not find pid file for osd.%s' % num)
        return True

    def start_mon_daemon(self, context, num):
        if not self.stop_mon_daemon(context, num):
            return False
        mon_name = 'mon.%s' % num
        utils.execute('service', 'ceph', 'start', mon_name, run_as_root=True)
        return True

    def stop_mds_daemon(self, context, num):
        file_path = '/var/run/ceph/mds.%s.pid' % num
        if os.path.exists(file_path):
            self._kill_by_pid_file(file_path)
        else:
            LOG.info('Can not find pid file for mds.%s' % num)
        return True

    def get_mds_id(self, host=FLAGS.host):
        """Stop mds service on this host."""
        def __config_dict():
            config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
            cdict = config.as_dict()
            return cdict
        config_dict = __config_dict()
        # get osd_ids
        mds_id = None
        for section in config_dict:
            if section.startswith("mds."):
                if config_dict[section]['host'] == host:
                    mds_id = section.replace("mds.", "")
        return mds_id

    def stop_mds(self, context):
        mds_id = self.get_mds_id()
        if mds_id:
            self.stop_mds_daemon(context, mds_id)

    def start_mds_daemon(self, context, num):
        mds_name = 'mds.%s' % num
        utils.execute('service', 'ceph', 'start', mds_name, run_as_root=True)

    def start_monitor(self, context):
        # Get info from db.
        res = self._conductor_rpcapi.init_node_get_by_host(context, FLAGS.host)
        node_type = res.get('type', None)
        # get mon_id
        mon_id = None
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config_dict = config.as_dict()
        for section in config_dict:
            if section.startswith("mon."):
                if config_dict[section]['host'] == FLAGS.host:
                    mon_id = section.replace("mon.", "")

        # Try to start monitor service.
        if mon_id:
            LOG.info('>> start the monitor id: %s' % mon_id)
            if node_type and node_type.find('monitor') != -1:
                self.start_mon_daemon(context, mon_id)

    def start_osd(self, context):
        # Start all the osds on this node.
        osd_list = []
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config_dict = config.as_dict()

        for section in config_dict:
            if section.startswith("osd."):
                if config_dict[section]['host'] == FLAGS.host:
                    osd_id = section.replace("osd.", "")
                    osd_list.append(osd_id)

        LOG.info('osd_list = %s' % osd_list)

        def __start_osd(osd_id):
            utils.execute('start_osd', osd_id, run_as_root=True)

        thd_list = []
        for osd_id in osd_list:
            thd = utils.MultiThread(__start_osd, osd_id=osd_id)
            thd_list.append(thd)
        utils.start_threads(thd_list)

    def add_mds(self, context):
        LOG.info('add_mds')
        mds_id = self.get_mds_id()
        if mds_id:
            LOG.info('add_mds find mds on this node. Just start it.')
            self.start_mds(context)
            return

        # Change /etc/ceph.conf file.
        # Add new mds service.
        LOG.info('add_mds begin to create new mds.')
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config.add_mds_header()
        mds_id = config.get_mds_num()
        LOG.info('create new mds_id = %s' % mds_id)
        init_node_ref = db.init_node_get_by_host(context, FLAGS.host)
        hostip = init_node_ref['secondary_public_ip']
        config.add_mds(FLAGS.host, hostip, mds_id)
        config.save_conf()

        values = {'mds': 'yes'}
        db.init_node_update(context, init_node_ref['id'], values)

        # Generate new keyring.
        mds_path = '/var/lib/ceph/mds/ceph-%s' % mds_id
        utils.execute('mkdir', '-p', mds_path, run_as_root=True)
        #mds_key = '/etc/ceph/keyring.mds.%s' % mds_id
        mds_key = os.path.join(mds_path,'keyring')
        out = utils.execute('ceph', 'auth',
                      'get-or-create', 'mds.%d' % mds_id,
                      'mds', "allow",
                      'osd', "allow *",
                      'mon', "allow rwx",
                      run_as_root=True)[0]
        utils.write_file_as_root(mds_key, out, 'w')

        # Start mds service.
        self.start_mds(context)

    def start_mds(self, context):
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config_dict = config.as_dict()
        # mds_id
        mds_id = None
        for section in config_dict:
            if section.startswith("mds."):
                if config_dict[section]['host'] == FLAGS.host:
                    mds_id = section.replace("mds.", "")

        # Try to start monitor service.
        if mds_id:
            LOG.info('>> start the mds id: %s' % mds_id)
            try:
                utils.execute('ceph-mds', '-i', mds_id, run_as_root=True)
            except:
                LOG.info('Meets some error on start mds service.')

    def start_server(self, context, node_id):
        """ Start server.
            0. start monitor
            1. start all osd.
            2. unset osd noout.
        """
        res = self._conductor_rpcapi.init_node_get_by_id(context, node_id)
        service_id = res.get('service_id', None)
        node_type = res.get('type', None)
        host_ip = res.get('secondary_public_ip', None)
        host = res.get('host', None)
        LOG.debug('The server info: %s %s %s %s' %
                  (service_id, node_type, host_ip, host))
        # get mon_id
        self.start_monitor(context)
        self.start_mds(context)

        # Update status
        osd_states = self._conductor_rpcapi.\
                osd_state_get_by_service_id(context, service_id)
        if not len(osd_states) > 0:
            LOG.info("There is no osd on node %s" % node_id)
            return True

        # Begin to start all the OSDs.
        def __start_osd(osd_name):
            osd_id = osd_name.split('.')[-1]
            self.start_osd_daemon(context, osd_id)
            values = {'state': FLAGS.osd_in_up, 'osd_name': osd_name}
            self._conductor_rpcapi.osd_state_update_or_create(context,
                                                              values)

        thd_list = []
        for item in osd_states:
            osd_name = item['osd_name']
            thd = utils.MultiThread(__start_osd, osd_name=osd_name)
            thd_list.append(thd)
        utils.start_threads(thd_list)

        #TODO Unset osd noout when all osd started
        count = db.init_node_count_by_status(context, 'Stopped')
        if count == 0:
            utils.execute('ceph', 'osd', 'unset', 'noout', run_as_root=True)

        # update init node status
        ret = self._conductor_rpcapi.\
                init_node_update_status_by_id(context, node_id,
                                                'Active')
        return True

    def track_monitors(self, mon_id):
        """Return the status of monitor in quorum."""
        # ceph --cluster=ceph \
        #      --admin-daemon \
        #      /var/run/ceph/ceph-mon.%id.asok \
        #        mon_status
        out = utils.execute('ceph',
                            '--cluster=ceph',
                            '--admin-daemon',
                            '/var/run/ceph/ceph-mon.%s.asok' % mon_id,
                            'mon_status',
                            run_as_root=True)[0]
        return json.loads(out)

    def create_keyring(self, mon_id):
        """Create keyring file:
            ceph.client.admin.keyring
            bootstrap-osd/keyring
            bootstrap-mds/keyrong
        """
        # Firstly begin to create ceph.client.admin.keyring
        utils.execute('ceph',
                      '--cluster=ceph',
                      '--name=mon.',
                      '--keyring=/var/lib/ceph/mon/mon{mon_id}/keyring'.format(
                          mon_id=mon_id,
                          ),
                      'auth',
                      'get-or-create',
                      'client.admin',
                      'mon', 'allow *',
                      'osd', 'allow *',
                      'mds', 'allow',
                      '-o',
                      '/etc/ceph/keyring.admin',
                      run_as_root=True)

        # Begin to create bootstrap keyrings.
        utils.execute('mkdir',
                      '-p',
                      '/var/lib/ceph/bootstrap-osd',
                      run_as_root=True)

        utils.execute('ceph',
                      '--cluster=ceph',
                      'auth',
                      'get-or-create',
                      'client.bootstrap-osd',
                      'mon',
                      'allow profile bootstrap-osd',
                      '-o',
                      '/var/lib/ceph/bootstrap-osd/ceph.keyring',
                      run_as_root=True)

        # Begin to create bootstrap-mds
        utils.execute('mkdir',
                      '-p',
                      '/var/lib/ceph/bootstrap-mds',
                      run_as_root=True)

        utils.execute('ceph',
                      '--cluster=ceph',
                      'auth',
                      'get-or-create',
                      'client.bootstrap-mds',
                      'mon',
                      'allow profile bootstrap-mds',
                      '-o',
                      '/var/lib/ceph/bootstrap-mds/ceph.keyring',
                      run_as_root=True)

    def stop_server(self, context, node_id):
        """Stop server.
           0. Remove monitor if it is a monitor
           1. Get service_id by node_id
           2. Get all osds for given service_id
           3. Set osd noout
           4. service ceph stop osd.$num
        """
        LOG.info('agent/driver.py stop_server')
        cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        LOG.info('Step 1. Scan the osds in db.')
        res = self._conductor_rpcapi.init_node_get_by_id(context, node_id)
        service_id = res.get('service_id', None)
        osd_states = self._conductor_rpcapi.\
                osd_state_get_by_service_id(context, service_id)
        if not len(osd_states) > 0:
            LOG.info("There is no osd on node %s" % node_id)
            return True

        LOG.info('Step 2. ceph osd set noout')
        utils.execute('ceph', 'osd', 'set', 'noout', run_as_root=True)
        for item in osd_states:
            osd_name = item['osd_name']
            LOG.info('>> service ceph stop %s' % osd_name)
            utils.execute('service', 'ceph', 'stop', osd_name,
                            run_as_root=True)
            values = {'state': 'DOWN', 'osd_name': osd_name}
            LOG.info('>> update status into db %s' % osd_name)
            self._conductor_rpcapi.\
                    osd_state_update_or_create(context, values)

        # Stop mds service.
        self.remove_mds(context, node_id)
        self._conductor_rpcapi.\
                init_node_update_status_by_id(context, node_id,
                                                'Stopped')
        values = {'mds': 'no'}
        self._conductor_rpcapi.init_node_update(context,
                                                node_id,
                                                values)
        return True

    def get_ceph_health(self, context):
        out, err = utils.execute('ceph',
                                 'health',
                                 run_as_root=True)
        if not 'HEALTH_OK' in out and not 'HEALTH_WARN' in out:
            LOG.info('Failed to start ceph cluster: %s' % out)
            try:
                raise exception.StartCephFaild
            except exception.StartCephFaild, e:
                LOG.error("%s:%s" %(e.code, e.message))
            return True
        return True

    def get_ceph_admin_keyring(self, context):
        """
        read ceph keyring from CEPH_PATH
        """
        with open(FLAGS.keyring_admin, "r") as fp:
            keyring_str = fp.read()
        return keyring_str

    def save_ceph_admin_keyring(self, context, keyring_str):
        """
        read ceph keyring from CEPH_PATH
        """
        open(FLAGS.keyring_admin, 'w').write(keyring_str)
        return True

    def refresh_osd_number(self, context):
        LOG.info("Start Refresh OSD number ")
        config_dict = cephconfigparser.CephConfigParser(FLAGS.ceph_conf).as_dict()
        osd_num_dict = {}

        for section in config_dict:
            if section.startswith("osd."):
                host = config_dict[section]['host']
                if not host in config_dict:
                    osd_num_dict.setdefault(host,  0)
                osd_num_dict[host] += 1
        LOG.info("Refresh OSD number %s " % osd_num_dict)

        init_nodes = self._conductor_rpcapi.get_server_list(context)
        init_node_dict = {}
        for node in init_nodes:
            init_node_dict.setdefault(node['host'], node)

        for host in osd_num_dict:
            values = {"data_drives_number": osd_num_dict[host]}
            self._conductor_rpcapi.init_node_update(context,
                                                    init_node_dict[host],
                                                    values)
        LOG.info("Refresh OSD number finish")
        return True

    def _remove_osd(self, context, osd_id, host_is_running=True):
        def _get_line(osd_id):
            out = utils.execute('ceph',
                                'osd',
                                'dump',
                                '-f',
                                'json-pretty',
                                run_as_root=True)[0]
            status = json.loads(out)
            for x in status['osds']:
                if int(x['osd']) == int(osd_id):
                    return x
            return None

        def _wait_osd_status(osd_id, key, value):
            status = _get_line(osd_id)
            if not status:
                time.sleep(10)
                return

            try_times = 0
            while str(status[key]) != str(value):
                try_times = try_times + 1
                if try_times > 120:
                    break

                status = _get_line(osd_id)
                if not status:
                    time.sleep(10)
                    return

                time.sleep(5)
                if try_times % 10 == 0:
                    LOG.info('Try %s: %s change key = %s to value = %s' % \
                            (try_times, osd_id, key, value))

        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)

        # Step 1: out this osd.
        LOG.info('>>> remove ceph osd osd_id %s' % osd_id)
        LOG.info('>>> remove ceph osd step0 out osd %s' % osd_id)
        utils.execute("ceph", "osd", "out", osd_id, run_as_root=True)
        _wait_osd_status(osd_id, 'in', 0)

        # Step 2: shutdown the process.
        if host_is_running:
            LOG.info('>>> remove ceph osd kill proc osd %s' % osd_id)
            utils.execute("service", "ceph", "-a", "stop", "osd.%s" % osd_id,
                      run_as_root=True)
        _wait_osd_status(osd_id, 'up', 0)

        # Step 3: Remove it from crushmap.
        LOG.info('>>> remove ceph osd step1 osd_id %s' % osd_id)
        utils.execute("ceph", "osd", "crush", "remove", "osd.%s" % osd_id,
                        run_as_root=True)

        # Step 4: Remove it from auth list.
        LOG.info('>>> remove ceph osd step2 osd_id %s' % osd_id)
        utils.execute("ceph", "auth", "del", "osd.%s" % osd_id,
                        run_as_root=True)

        # Step 5: rm it.
        LOG.info('>>> remove ceph osd step3 osd_id %s' % osd_id)
        utils.execute("ceph", "osd", "rm", osd_id, run_as_root=True)

        # Step 6: Remove it from ceph.conf
        LOG.info('>>> remove ceph osd step4 osd_id %s' % osd_id)
        config.remove_osd(osd_id)
        config.save_conf(FLAGS.ceph_conf)

    def osd_remove(self, context, osd_id, device, umount_path):
        LOG.info('osd_remove osd_id = %s' % osd_id)
        self._remove_osd(context, osd_id)
        utils.execute("umount",
                      umount_path,
                      check_exit_code=False,
                      run_as_root=True)
        return True

    def ceph_osd_stop(self, context, osd_name):
        utils.execute('service',
                      'ceph',
                      '-a',
                      'stop',
                      osd_name,
                      run_as_root=True)
        #osd_id = osd_name.split('.')[-1]
        #values = {'state': 'Out-Down', 'osd_name': osd_name}
        #ret = self._conductor_rpcapi.\
        #        osd_state_update_or_create(context, values)

    def ceph_osd_start(self, context, osd_name):
        osd_id = osd_name.split('.')[-1]
        self.start_osd_daemon(context, osd_id)
        #values = {'state': FLAGS.osd_in_up, 'osd_name': osd_name}
        #ret = self._conductor_rpcapi.\
        #        osd_state_update_or_create(context, values)

    def osd_restart(self, context, osd_id):
        LOG.info('osd_restart osd_id = %s' % osd_id)
        osd = db.osd_get(context, osd_id)
        #stop
        utils.execute('ceph', 'osd', 'set', 'noout', run_as_root=True)
        self.ceph_osd_stop(context, osd['osd_name'])
        #start
        utils.execute('ceph', 'osd', 'unset', 'noout', run_as_root=True)
        self.ceph_osd_start(context, osd['osd_name'])
        time.sleep(10)
        return True

    def osd_restore(self, context, osd_id):
        LOG.info('osd_restore osd_id = %s' % osd_id)
        osd = db.osd_get(context, osd_id)
        init_node = db.init_node_get_by_service_id(context, osd['service_id'])
        osd_conf_dict = {"host": FLAGS.host,
                        "primary_public_ip": init_node['primary_public_ip'],
                        "secondary_public_ip": init_node['secondary_public_ip'],
                        "cluster_ip": init_node['cluster_ip'],
                        "dev_name": osd['device']['name'],
                        "dev_journal": osd['device']['journal'],
                        "file_system": osd['device']['fs_type']}
        LOG.debug('osd_conf_dict = %s' % osd_conf_dict)
        stdout = utils.execute("ceph",
                               "osd",
                               "create",
                               run_as_root=True)[0]

        osd_inner_id = str(int(stdout))
        osd_name = 'osd.%s' % osd_inner_id

        LOG.info("new osd_name = %s" % osd_name)

        utils.execute("umount",
                      osd['device']['name'],
                      check_exit_code=False,
                      run_as_root=True)

        file_system = 'xfs'
        if osd['device']['fs_type']:
            file_system = osd['device']['fs_type']

        mkfs_option = utils.get_fs_options(file_system)[0]
        utils.execute("mkfs",
                      "-t", file_system,
                      mkfs_option,
                      osd['device']['name'],
                      run_as_root=True)

        #osd_pth = '%sceph-%s' % (FLAGS.osd_data_path, osd_inner_id)
        osd_pth = '/var/lib/ceph/osd/osd%s' % osd_inner_id
        utils.ensure_tree(osd_pth)
        fs_opt = utils.get_fs_options(file_system)[1]
        utils.execute("mount",
                      "-t", file_system,
                      "-o", fs_opt,
                      osd['device']['name'],
                      osd_pth,
                      run_as_root=True)

        self._clean_dirs(osd_pth)

        self._add_ceph_osd_to_config(context, osd_conf_dict, osd_inner_id)
        utils.execute("ceph-osd",
                      "-i", osd_inner_id,
                      "--mkfs",
                      "--mkkey",
                      run_as_root=True)

        utils.execute("ceph", "auth", "del", "osd.%s" % osd_inner_id,
                        run_as_root=True)
        osd_keyring_pth = "/etc/ceph/keyring.osd.%s" % osd_inner_id
        utils.execute("ceph", "auth", "add", "osd.%s" % osd_inner_id,
                      "osd", "allow *", "mon", "allow rwx",
                      "-i", osd_keyring_pth,
                      run_as_root=True)

        storage_group = osd['storage_group']['name']

        #TODO change zone
        zone = init_node['zone']['name']
        crush_dict = {"root": 'vsm',
                    "storage_group":storage_group,
                    "zone": "_".join([zone, storage_group]),
                    "host": "_".join([FLAGS.host, storage_group, zone]),
                    }
        weight = "1.0"
        utils.execute("ceph",
                      "osd",
                      "crush",
                      "add",
                      "osd.%s" % osd_inner_id,
                      weight,
                      "root=%s" % crush_dict['root'],
                      "storage_group=%s" % crush_dict['storage_group'],
                      "zone=%s" % crush_dict['zone'],
                      "host=%s" % crush_dict['host'],
                      run_as_root=True)

        #step1
        self.start_osd_daemon(context, osd_inner_id)
        #step2
        utils.execute('ceph', 'osd', 'in', osd_name, run_as_root=True)
        time.sleep(10)
        #update db
        value = {}
        value['id'] = osd_id
        value['osd_name'] = osd_name
        value['operation_status'] = FLAGS.vsm_status_present
        value['state'] = FLAGS.osd_in_up
        db.osd_state_update(context, osd_id, value)
        return True

    def set_pool_pg_pgp_num(self, context, pool, pg_num, pgp_num):
        self.set_pool_pg_num(context, pool, pg_num)
        #need to wait for the last set pg_num
        time.sleep(120)
        self.set_pool_pgp_num(context, pool, pgp_num)
        
    def set_pool_pg_num(self, context, pool, pg_num):
        args= ['ceph', 'osd', 'pool', 'set', pool, 'pg_num', pg_num]
        utils.execute(*args, run_as_root=True)

    def set_pool_pgp_num(self, context, pool, pgp_num):
        args= ['ceph', 'osd', 'pool', 'set', pool, 'pgp_num', pgp_num]
        utils.execute(*args, run_as_root=True)

    def get_osds_status(self):
        args = ['ceph', 'osd', 'dump', '-f', 'json']
        #args = ['hostname', '-I']
        #(out, _err) = utils.execute(*args)
        (out, _err) = utils.execute(*args, run_as_root=True)
        if out != "":
            #LOG.info("osd_status:%s", out)
            return out
        else:
            return None

    def get_ceph_health_list(self):
        args = ['ceph', 'health']
        out, _err = utils.execute(*args, run_as_root=True)
        try:
            k = out.find(" ")
            status = out[:k]
            health_list =[i.strip() for i in out[k:].split(";")]
            return [status] + health_list
        except:
            return ["GET CEPH STATUS ERROR"]

    def make_cmd(self, args):
        h_list = list()
        t_list = ['-f', 'json-pretty']
        if isinstance(args, list):
            h_list.extend(args)
            h_list.extend(t_list)
        else:
            h_list.append(args)
            h_list.append(t_list)

        return h_list

    def _run_cmd_to_json(self, args, pretty=True):
        if pretty:
            cmd = self.make_cmd(args)
        else:
            cmd = args
        #LOG.debug('command is %s' % cmd)
        (out, err) = utils.execute(*cmd, run_as_root=True)
        json_data = None
        if out:
            json_data = json.loads(out)
        return json_data

    def get_osds_total_num(self):
        args = ['ceph', 'osd', 'ls']
        osd_list = self._run_cmd_to_json(args)
        return len(osd_list)
 
    def get_crushmap_nodes(self):
        args = ['ceph', 'osd', 'tree']
        node_dict = self._run_cmd_to_json(args)
        node_list = []
        if node_dict:
            node_list = node_dict.get('nodes')
        return node_list

    def get_osds_tree(self):
        return_list = list()
        node_list = self.get_crushmap_nodes()
        if node_list:
            for node in node_list:
                name = node.get('name')
                if name and name.startswith('osd.'):
                    #LOG.debug('node %s ' % node)
                    return_list.append(node)
        #LOG.debug('osd list: %s' % return_list)
        return return_list

    def get_osd_capacity(self):
        args = ['ceph', 'pg', 'dump', 'osds']
        osd_dict = self._run_cmd_to_json(args)
        #LOG.debug('osd list: %s' % osd_dict)
        return osd_dict

    def get_pool_status(self):
        args = ['ceph', 'osd', 'dump']
        dump_list = self._run_cmd_to_json(args)
        if dump_list:
            return dump_list.get('pools')
        return None

    def get_pool_usage(self):
        args = ['ceph', 'pg', 'dump', 'pools']
        return self._run_cmd_to_json(args)

    def get_pool_stats(self):
        args = ['ceph', 'osd', 'pool', 'stats']
        return self._run_cmd_to_json(args)

    def get_osd_lspools(self):
        args = ['ceph', 'osd', 'lspools']
        pool_list = self._run_cmd_to_json(args)
        return pool_list

    def get_rbd_lsimages(self, pool):
        #args = ['rbd', 'ls', '-l', pool, \
        #       '--format', 'json', '--pretty-format']
        args = ['rbd_ls', pool] 
        rbd_image_list = self._run_cmd_to_json(args, pretty=False)
        return rbd_image_list

    def get_rbd_image_info(self, image, pool):
        args = ['rbd', '--image', \
                 image,\
                 '-p', pool, \
                 '--pretty-format',\
                 '--format', 'json', \
                 'info']
        rbd_image_dict = self._run_cmd_to_json(args, pretty=False)
        return rbd_image_dict
 
    def get_rbd_status(self):
        pool_list = self.get_osd_lspools()
        if pool_list:
            rbd_list = []
            for pool in pool_list:
                rbd_image_list = self.get_rbd_lsimages(pool['poolname'])
                if rbd_image_list:
                    for rbd_image in rbd_image_list:
                        rbd_dict = {}
                        image_dict = self.get_rbd_image_info(\
                                     rbd_image['image'], \
                                     pool['poolname'])
                        if image_dict:
                            rbd_dict['pool'] = pool['poolname']
                            rbd_dict['image'] = rbd_image['image']
                            rbd_dict['size'] = rbd_image['size']
                            rbd_dict['format'] = rbd_image['format']
                            rbd_dict['objects'] = image_dict['objects']
                            rbd_dict['order'] = image_dict['order']
                            rbd_list.append(rbd_dict)
            return rbd_list
        else:
            return None

    def get_mds_dump(self):
        args = ['ceph', 'mds', 'dump']
        mds_dict = self._run_cmd_to_json(args)
        return mds_dict

    def get_mds_status(self):
        mds_dict = self.get_mds_dump()
        if mds_dict:
            mds_list = []
            for key in mds_dict['info'].keys():
                dict = {}
                item = mds_dict['info'][key]
                dict['gid'] = item['gid']
                dict['name'] = item['name']
                dict['state'] = item['state']
                dict['address'] = item['addr']
                mds_list.append(dict)
            return mds_list
        else:
            return

    def get_pg_dump(self):
        args = ['ceph', 'pg', 'dump', 'pgs_brief']
        result = self._run_cmd_to_json(args)
        return result

    def get_pg_status(self):
        val_list = self.get_pg_dump()
        if val_list:
            pg_list = []
            for item in val_list:
                dict = {}
                dict['pgid'] = item['pgid']
                dict['state'] = item['state']
                dict['up'] = ','.join(str(v) for v in item['up'])
                dict['acting'] = ','.join(str(v) for v in item['acting'])
                pg_list.append(dict)
            return pg_list
        else:
            return

    def get_mon_health(self):
        args = ['ceph', 'health']
        return self._run_cmd_to_json(args)

    def get_ceph_status(self):
        args = ['ceph', 'status']
        return self._run_cmd_to_json(args)

    def get_crush_rule_dump_by_name(self, name):
        args = ['ceph', 'osd', 'crush', 'rule', 'dump', name]
        return self._run_cmd_to_json(args)

    def get_summary(self, sum_type, sum_dict=None):
        if sum_type in [FLAGS.summary_type_pg, FLAGS.summary_type_osd,
                        FLAGS.summary_type_mds, FLAGS.summary_type_mon,
                        FLAGS.summary_type_cluster, FLAGS.summary_type_vsm]:
            if not sum_dict:
                sum_dict = self.get_ceph_status()

            if sum_dict:
                if sum_type == FLAGS.summary_type_pg:
                    return self._pg_summary(sum_dict)
                elif sum_type == FLAGS.summary_type_osd:
                    return self._osd_summary(sum_dict)
                elif sum_type == FLAGS.summary_type_mds:
                    return self._mds_summary(sum_dict)
                elif sum_type == FLAGS.summary_type_mon:
                    return self._mon_summary(sum_dict)
                elif sum_type == FLAGS.summary_type_cluster:
                    return self._cluster_summary(sum_dict)
                elif sum_type == FLAGS.summary_type_vsm:
                    return self._vsm_summary(sum_dict)

    def _osd_summary(self, sum_dict):
        if sum_dict:
            osdmap = sum_dict.get('osdmap')
            return json.dumps(osdmap)
        return None

    def _pg_summary(self, sum_dict):
        if sum_dict:
            pgmap = sum_dict.get('pgmap')
            return json.dumps(pgmap)
        return None

    def _mds_summary(self, sum_dict):
        if sum_dict:
            mdsmap = sum_dict.get('mdsmap')
            mds_dict = self.get_mds_dump()
            if mds_dict:
                mdsmap['failed'] = len(mds_dict['failed'])
                mdsmap['stopped'] = len(mds_dict['stopped'])
            else:
                mdsmap['failed'] = -1
                mdsmap['stopped'] = -1
            return json.dumps(mdsmap)
        return None

    def _mon_summary(self, sum_dict):
        if sum_dict:
            mon_data = {
                'monmap_epoch': sum_dict.get('monmap').get('epoch'),
                'monitors': len(sum_dict.get('monmap').get('mons')),
                'election_epoch': sum_dict.get('election_epoch'),
                'quorum': json.dumps(' '.join(sum_dict.get('quorum_names'))).strip('"'),
                'overall_status': json.dumps(sum_dict.get('health').get('overall_status')).strip('"')
            }
            return json.dumps(mon_data)

    def _cluster_summary(self, sum_dict):
        if sum_dict:
            cluster_data = {
                'cluster': sum_dict.get('fsid'),
                'status': sum_dict.get('health').get('summary'),
                'detail': sum_dict.get('health').get('detail'),
                'health_list': sum_dict.get("health_list")
            }
            return json.dumps(cluster_data)

    def _vsm_summary(self, sum_dict):
        #TODO: run cmd uptime | cut -d ' ' -f2
        try:
            uptime = open("/proc/uptime", "r").read().strip().split(" ")[0]
        except:
            uptime = ""
        return json.dumps({
            'uptime': uptime,
        })

    def ceph_status(self):
        is_active = True
        try:
            self.get_ceph_status()
        except exception.ProcessExecutionError as e:
            LOG.debug('exit_code: %s, stderr: %s' % (e.exit_code, e.stderr))
            if e.exit_code == 1 and e.stderr.find('TimeoutError') != -1:
                is_active = False
        return json.dumps({
            'is_ceph_active': is_active
        })

    def add_cache_tier(self, context, body):
        storage_pool_name = db.pool_get(context, body.get("storage_pool_id")).get('name')
        cache_pool_name = db.pool_get(context, body.get("cache_pool_id")).get('name')
        cache_mode = body.get("cache_mode")
        LOG.info("add cache tier start")
        LOG.info("storage pool %s cache pool %s " % (storage_pool_name, cache_pool_name))

        if body.get("force_nonempty"):
            utils.execute("ceph", "osd", "tier", "add", storage_pool_name, \
                      cache_pool_name, "--force-nonempty",  run_as_root=True)
        else:
            utils.execute("ceph", "osd", "tier", "add", storage_pool_name, \
                          cache_pool_name, run_as_root=True)
        utils.execute("ceph", "osd", "tier", "cache-mode", cache_pool_name, \
                      cache_mode, run_as_root=True)
        if cache_mode == "writeback":
            utils.execute("ceph", "osd", "tier", "set-overlay", storage_pool_name, \
                          cache_pool_name, run_as_root=True)

        db.pool_update(context, body.get("storage_pool_id"), {"cache_tier_status": "Storage pool for:%s" % cache_pool_name})
        db.pool_update(context, body.get("cache_pool_id"), {
            "cache_tier_status": "Cache pool for:%s" % storage_pool_name,
            "cache_mode": cache_mode})

        options = body.get("options")
        self._configure_cache_tier(cache_pool_name, options)
        LOG.info("add cache tier end")

        return True

    def _configure_cache_tier(self, cache_pool_name, options):
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "hit_set_type", options["hit_set_type"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "hit_set_count", options["hit_set_count"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "hit_set_period", options["hit_set_period_s"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "target_max_bytes", int(options["target_max_mem_mb"]) * 1000000, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "cache_target_dirty_ratio", options["target_dirty_ratio"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "cache_target_full_ratio", options["target_full_ratio"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "target_max_objects", options["target_max_objects"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "cache_min_flush_age", options["target_min_flush_age_m"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "cache_min_evict_age", options["target_min_evict_age_m"], run_as_root=True)

    def remove_cache_tier(self, context, body):
        LOG.info("Remove Cache Tier")
        LOG.info(body)
        cache_pool = db.pool_get(context, body.get("cache_pool_id"))
        cache_pool_name = cache_pool.get("name")
        storage_pool_name = cache_pool.get("cache_tier_status").split(":")[1].strip()
        LOG.info(cache_pool['name'])
        LOG.info(cache_pool['cache_mode'])
        cache_mode = cache_pool.get("cache_mode")
        LOG.info(cache_mode)
        if cache_mode == "writeback":
            utils.execute("ceph", "osd", "tier", "cache-mode", cache_pool_name, \
                          "forward", run_as_root=True)
            utils.execute("rados", "-p", cache_pool_name, "cache-flush-evict-all", \
                          run_as_root=True)
            utils.execute("ceph", "osd", "tier", "remove-overlay", storage_pool_name, \
                          run_as_root=True)
        else:
            utils.execute("ceph", "osd", "tier", "cache-mode", cache_pool_name, \
                          "none", run_as_root=True)
        utils.execute("ceph", "osd", "tier", "remove", storage_pool_name, \
                      cache_pool_name, run_as_root=True)
        db.pool_update(context, cache_pool.pool_id, {"cache_tier_status": None})
        # TODO cluster id
        db.pool_update_by_name(context, storage_pool_name, 1, {"cache_tier_status": None})
        return True


class DbDriver(object):
    """Executes commands relating to TestDBs."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        pass

    def init_host(self, host):
        pass

    def update_recipe_info(self, context):
        LOG.info("DEBUG in update_recipe_info() in DbDriver()")
        res = db.recipe_get_all(context)
        recipe_id_list = []
        for x in res:
            recipe_id_list.append(int(x.recipe_id))
   
        str0 = os.popen("ssh root@10.239.82.125 \'ceph osd lspools\' ").read()
        str = str0[0:-2]
        LOG.info('DEBUG str from mon %s' % str)
        items = str.split(',')
        ##
        items.remove('5 -help')
        LOG.info("DEBUG items %s" % items)
        ## 
        pool_name_list = []
        attr_names = ['size', 'min_size', 'crash_replay_interval', 'pg_num',
                     'pgp_num', 'crush_ruleset',]
 
        for item in items:
            x = item.split()
            pool_name_list.append(x[1])
            pool_name = x[1]
            pool_id = int(x[0])
            values = {}
            values['recipe_name'] = pool_name
            for attr_name in attr_names:
                val = os.popen("ssh root@10.239.82.125 \'ceph osd pool\
                                get %s %s\'" % (pool_name, attr_name)).read()
                LOG.info("DEBUG val from cmon %s" % val)
                _list = val.split(':')
                values[attr_name] = int(_list[1])
            if pool_id in recipe_id_list:
                LOG.info('DEBUG update pool: %s recipe values %s' % (pool_name, values))
                db.recipe_update(context, pool_id, values)
            else:
                values['recipe_id'] = pool_id
                LOG.info('DEBUG create pool: %s recipe values %s' % (pool_name, values))
                db.recipe_create(context, values)

    def update_pool_info(self, context):
        LOG.info("DEBUG in update_pool_info() in DbDriver()")
        attr_names = ['size', 'min_size', 'crash_replay_interval', 'pg_num',
                     'pgp_num', 'crush_ruleset',]
        res = db.pool_get_all(context)
        pool_list = []
        for x in res:
            pool_list.append(int(x.pool_id))
            LOG.info('x.id = %s' % x.pool_id)

        #str0 = "0 data,1 metadata,2 rbd,3 testpool_after_periodic"
        str0 = os.popen("ssh root@10.239.82.125 \'ceph osd lspools\' ").read()
        str = str0[0:-2]
        items = str.split(',')
        LOG.info("DEBUG items %s pool_list %s" % (items, pool_list))
        for i in items:
            x = i.split()
            values = {}
            pool_id = int(x[0])
            LOG.info('DEBUG x[0] %s' % pool_id)
            pool_name = x[1]
            for attr_name in attr_names:
                val = os.popen("ssh root@10.239.82.125 \'ceph osd pool\
                                get %s %s\'" % (pool_name, attr_name)).read()
                LOG.info("DEBUG val from cmon %s" % val)
                _list = val.split(':')
                values[attr_name] = int(_list[1])

            if pool_id in pool_list:
                #pool_id = x[0]
                values['name'] = x[1]
                db.pool_update(context, pool_id, values)
            else:
                values['pool_id'] = pool_id
                values['name'] = x[1]
                values['recipe_id'] = pool_id
                values['status'] = 'running'
                db.pool_create(context, values)

        return res

class CreateCrushMapDriver(object):
    """Create crushmap file"""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        self.conductor_api = conductor.API()
        self.conductor_rpcapi = conductor_rpcapi.ConductorAPI()
        self.osd_num = 0
        self._crushmap_path = "/tmp/crushmap"
        fd = open(self._crushmap_path, 'w')
        fd.write("")
        fd.close()

    def _write_to_crushmap(self, string):
        fd = open(self._crushmap_path, 'a')
        fd.write(string)
        fd.close()

    def add_new_zone(self, context, zone_name):
        res = self.conductor_api.storage_group_get_all(context)
        storage_groups = []
        for i in res:
            storage_groups.append(i["name"])
        storage_groups = list(set(storage_groups))

        for storage_group in storage_groups:
            zone = zone_name + "_" + storage_group
            utils.execute("ceph", "osd", "crush", "add-bucket", zone, "zone",
                            run_as_root=True)
            utils.execute("ceph", "osd", "crush", "move", zone,
                          "storage_group=%s" % storage_group,
                          run_as_root=True)

        values = {'name': zone_name,
                  'deleted': 0}
        self.conductor_rpcapi.create_zone(context, values)
        return True

    def add_rule(self, name, type):
        utils.execute("ceph", "osd", "crush", "rule", "create-simple", \
                        name, name, type)
        
    def add_storage_group(self, storage_group, root):
        utils.execute("ceph", "osd", "crush", "add-bucket", storage_group, \
                        "storage_group", run_as_root=True)
        utils.execute("ceph", "osd", "crush", "move", storage_group,\
                        "root=%s" % root, run_as_root=True)

    def add_zone(self, zone, storage_group):
        utils.execute("ceph", "osd", "crush", "add-bucket", zone, \
                        "zone", run_as_root=True)
        utils.execute("ceph", "osd", "crush", "move", zone, \
                        "storage_group=%s" % storage_group, run_as_root=True)
 
    def add_host(self, host_name, zone):
        utils.execute("ceph", "osd", "crush", "add-bucket", host_name, "host",
                        run_as_root=True)
        utils.execute("ceph", "osd", "crush", "move", host_name,
                        "zone=%s" % zone,
                        run_as_root=True)

    def remove_host(self, host_name):
        utils.execute("ceph", "osd", "crush", "remove", host_name,
                        run_as_root=True)

    def create_crushmap(self, context, server_list):
        LOG.info("DEBUG Begin to create crushmap file in /tmp/crushmap")
        LOG.info("DEBUG in create_crushmap body is %s" % server_list)
        service_id = []
        for i in server_list:
            if i["is_storage"]:
                service_id.append(i["id"])
        #service id is init node id
        LOG.info("init node id list %s" % service_id)

        osd_num = 0
        for id in service_id:
            res = self.conductor_api.osd_state_count_by_init_node_id(context, id)
            osd_num = osd_num + int(res)
        init_node = db.init_node_get(context, service_id[0])
        zone_tag = True
        if init_node['zone']['name'] == FLAGS.default_zone:
            zone_tag = False 
        self._gen_crushmap_optimal()
        self._gen_device_osd(osd_num)
        self._gen_bucket_type()
        self._gen_bucket(context, service_id)
        self._generate_rule(context, zone_tag)
        LOG.info('Create crushmap over')
        return True

    def set_crushmap(self, context):
        LOG.info("DEBUG Begin to set crushmap")
        utils.execute('crushtool', '-c', '/tmp/crushmap', '-o',
                        '/tmp/compiled_crushmap', run_as_root=True)
        utils.execute('ceph', 'osd', 'setcrushmap', '-i',
                        '/tmp/compiled_crushmap', run_as_root=True)

        #the following is zone version to solve "active_remaped" etc.Don't delete it! 
        #utils.execute('crushtool', '-c', '/tmp/crushmap', 
        #                '--enable-unsafe-tunables',
        #                '--set-choose-local-tries','0',
        #                '--set-choose-local-fallback-tries', '0',
        #                '--set-choose-total-tries', '50', '-o',
        #                '/tmp/compiled_crushmap', run_as_root=True)
        #utils.execute('ceph', 'osd', 'setcrushmap', '-i',
        #                '/tmp/compiled_crushmap', run_as_root=True)
        # TODO return success here.
        return True

    def _gen_crushmap_optimal(self):
        optimal = "# begin crush map\ntunable choose_local_tries 0\
                  \ntunable choose_local_tries 0\ntunable choose_total_tries 50\
                  \ntunable chooseleaf_descend_once 1\ntunable chooseleaf_vary_r 1\n"
        self._write_to_crushmap(optimal)

    def _gen_device_osd(self, osd_num):
        self._write_to_crushmap("\n# devices\n")
        for i in range(0, osd_num):
            string = "device " + str(i) + " osd." + str(i) + "\n"
            self._write_to_crushmap(string)

    def _gen_bucket_type(self):
        string = "\n#types\ntype 0 osd\ntype 1 host\ntype 2 zone\
                  \ntype 3 storage_group\ntype 4 root\n\n"
        self._write_to_crushmap(string)

    def _gen_bucket(self, context, service_id):
        res = self.conductor_api.storage_group_get_all(context)
        storage_groups = []
        for i in res:
            storage_groups.append(i["name"])
        storage_groups = list(set(storage_groups))

        LOG.info("storage_groups is: %s " % storage_groups)
        res = self.conductor_api.zone_get_all(context)
        zones = []
        for i in res:
            zones.append(i["name"])

        hosts = []
        for id in service_id:
            res = self.conductor_api.init_node_get_by_id(context, id)
            hosts.append(res["host"])

        node_info = []
        LOG.info("DEB-YOU %s " % service_id)
        for id in service_id:
            res = self.conductor_api.\
                  ceph_node_info(context, id)
            for j in res:
                node_info.append(j)
        LOG.info("AGENT node info %s" % node_info)

        num = 0
        host_bucket, num = self._get_host_dic(node_info, storage_groups,\
                                             zones, service_id, num, context)
        self._write_host_bucket(host_bucket)
        zone_bucket, num = self._get_zone_dic(node_info, host_bucket,\
                                         zones, storage_groups, num)
        self._write_zone_bucket(zone_bucket)
        storage_group_bucket, num = self._get_storage_group_bucket(storage_groups,\
                                                             zone_bucket, num)
        self._write_storage_group_bucket(storage_group_bucket)
        root_bucket, num = self._get_root_bucket(storage_group_bucket, num)
        self._write_root_bucket(root_bucket)

    def _get_host_dic(self, node_info, storage_groups, zones, service_id, num, context):
        host = []
        LOG.info("service id %s " % service_id)
        for id in service_id:
            res = self.conductor_api.init_node_get_by_id(context, id)
            host_name = res["host"]
            id2 = res["zone_id"]
            res = self.conductor_api.zone_get_by_id(context, id2)
            zone = res["name"]
            for storage_group in storage_groups:
                dic = {}
                dic["name"] = host_name + "_" + storage_group + "_" + zone
                dic["zone"] = zone
                dic["storage_group"] = storage_group
                dic["id"] = num - 1
                num = num -1
                items = []
                weight = 0
                for node in node_info:
                    if node["host"] == host_name and node["storage_group_name"] == storage_group:
                        items.append(node["osd_state_name"])
                        weight = weight + 1
                dic["weight"] = (weight != 0 and weight or FLAGS.default_weight)
                dic["item"] = items
                host.append(dic)
        return host, num

    def _get_zone_dic(self, node_info, hosts, zones, storage_groups, num):
        zone_bucket = []
        for zone in zones:
            for storage_group in storage_groups:
                dic = {}
                dic["name"] = zone + "_" + storage_group
                dic["storage_group"] = storage_group
                items = []
                weight = 0
                for host in hosts:
                    if host["zone"] == zone and host["storage_group"] == storage_group:
                        item = {}
                        item["weight"] = host["weight"]
                        item["host_name"] = host["name"]
                        items.append(item)
                        weight = weight + host["weight"]
                dic["weight"] = (weight != 0 and weight or FLAGS.default_weight)
                dic["item"] = items
                num = num - 1
                dic["id"] = num
                zone_bucket.append(dic)
        return zone_bucket, num

    def _get_storage_group_bucket(self, storage_groups, zones, num):
        storage_group_bucket = []
        for storage_group in storage_groups:
            dic = {}
            dic["name"] = storage_group
            items = []
            weight = 0
            for zone in zones:
                if zone["storage_group"] == storage_group:
                    item = {}
                    item["weight"] = zone["weight"]
                    item["zone_name"] = zone["name"]
                    items.append(item)
                    weight = weight + zone["weight"]
            dic["weight"] = (weight != 0 and weight or FLAGS.default_weight)
            dic["item"] = items
            num = num - 1
            dic["id"] = num
            storage_group_bucket.append(dic)
        return storage_group_bucket, num

    def _get_root_bucket(self, storage_groups, num):
        root_bucket = []
        dic = {}
        dic["name"] = "vsm"
        items = []
        for storage_group in storage_groups:
            if storage_group["weight"] != 0:
                item = {}
                item["weight"] = storage_group["weight"]
                item["storage_group_name"] = storage_group["name"]
                items.append(item)
        dic["item"] = items
        num = num - 1
        dic["id"] = num
        root_bucket.append(dic)
        return root_bucket, num

    def _write_host_bucket(self, hosts):
        for host in hosts:
            self._write_to_crushmap("host " + host["name"] + " {\n")
            self._write_to_crushmap("    id " + str(host["id"]) + "\n")
            self._write_to_crushmap("    alg straw\n    hash 0\n")
            for item in host["item"]:
                self._write_to_crushmap("    item " + item + " weight 1.00\n")
            self._write_to_crushmap("}\n\n")

    def _write_zone_bucket(self, zones):
        for zone in zones:
            self._write_to_crushmap("zone " + zone["name"] + " {\n")
            self._write_to_crushmap("    id " + str(zone["id"]) + "\n")
            self._write_to_crushmap("    alg straw\n    hash 0\n")
            for item in zone["item"]:
                self._write_to_crushmap("    item " + item["host_name"] + \
                                " weight " + str(item["weight"]) + "\n")
            self._write_to_crushmap("}\n\n")

    def _write_storage_group_bucket(self, storage_groups):
        for storage_group in storage_groups:
            self._write_to_crushmap("storage_group " + storage_group["name"] + " {\n")
            self._write_to_crushmap("    id " + str(storage_group["id"]) + "\n")
            self._write_to_crushmap("    alg straw\n    hash 0\n")
            for item in storage_group["item"]:
                self._write_to_crushmap("    item " + item["zone_name"] + \
                                " weight " + str(item["weight"]) + "\n")
            self._write_to_crushmap("}\n\n")

    def _write_root_bucket(self, roots):
        for root in roots:
            self._write_to_crushmap("root " + root["name"] + " {\n")
            self._write_to_crushmap("    id " + str(root["id"]) + "\n")
            self._write_to_crushmap("    alg straw\n    hash 0\n")
            for item in root["item"]:
                self._write_to_crushmap("    item " + item["storage_group_name"] + \
                                " weight " + str(item["weight"]) + "\n")
            self._write_to_crushmap("}\n\n")

    def _key_for_sort(self, dic):
        return dic['rule_id']

    def _generate_rule(self, context, zone_tag):
        storage_groups = self.conductor_api.storage_group_get_all(context)
        if storage_groups is None:
            LOG.info("Error in getting storage_groups")
            try:
                raise exception.GetNoneError
            except exception.GetNoneError, e:
                LOG.error("%s:%s" %(e.code, e.message))
            return False
        LOG.info("DEBUG in generate rule begin")
        LOG.info("DEBUG storage_groups from conductor %s " % storage_groups)
        sorted_storage_groups = sorted(storage_groups, key=self._key_for_sort)
        LOG.info("DEBUG storage_groups after sorted %s" % sorted_storage_groups)
        sting_common = """    type replicated
    min_size 0
    max_size 10
"""
        if zone_tag:
            string_choose = """    step chooseleaf firstn 0 type zone
    step emit
}
"""
        else:
            string_choose = """    step chooseleaf firstn 0 type host
    step emit
}
"""
        for storage_group in sorted_storage_groups:
            storage_group_name = storage_group["name"]
            rule_id = storage_group["rule_id"]
            string = ""
            string = string + "\nrule " + storage_group_name + " {\n"
            string = string + "    ruleset " + str(rule_id) + "\n"
            string = string + sting_common
            string = string + "    step take " + storage_group_name + "\n"
            string = string + string_choose
            self._write_to_crushmap(string)

            #if storage_group_name.find("value_") == -1:
            #    string = ""
            #    string = string + "\nrule " + storage_group_name + " {\n"
            #    string = string + "    ruleset " + str(rule_id) + "\n"
            #    string = string + sting_common
            #    string = string + "    step take " + storage_group_name + "\n"
            #    string = string + string_choose
            #    self._write_to_crushmap(string)
            #else:
            #    string = ""
            #    string = string + "\nrule " + storage_group_name + " {\n"
            #    string = string + "    ruleset " + str(rule_id) + "\n"
            #    string = string + "    type replicated\n    min_size 0\n"
            #    string = string + "    max_size 10\n"
            #    string = string + "    step take " + storage_group_name + "\n"

            #    if zone_tag:
            #        string = string + "    step chooseleaf firstn 1 type zone\n"
            #    else:
            #        string = string + "    step chooseleaf firstn 1 type host\n"
            #    string = string + "    step emit\n"
            #    string = string + "    step take " + \
            #            storage_group_name.replace('value_', '') + "\n"

            #    if zone_tag:
            #        string = string + "    step chooseleaf firstn -1 type zone\n"
            #    else:
            #        string = string + "    step chooseleaf firstn -1 type host\n"
            #    string = string + "    step emit\n}\n" 
            #    self._write_to_crushmap(string)
        return True

    def _gen_rule(self):
        string = """\n# rules
rule capacity {
    ruleset 0
    type replicated
    min_size 0
    max_size 10
    step take capacity
    step chooseleaf firstn 0 type host
    step emit
}

rule performance {
    ruleset 1
    type replicated
    min_size 0
    max_size 10
    step take performance
    step chooseleaf firstn 0 type host
    step emit
}

rule high_performance {
    ruleset 2
    type replicated
    min_size 0
    max_size 10
    step take high_performance
    step chooseleaf firstn 0 type host
    step emit
}

rule value_capacity {
    ruleset 3
    type replicated
    min_size 0
    max_size 10
    step take value_capacity
    step chooseleaf firstn 1 type host
    step emit
    step take capacity
    step chooseleaf firstn -1 type host
    step emit
}

rule value_performance {
    ruleset 4
    type replicated
    min_size 0
    max_size 10
    step take value_performance
    step chooseleaf firstn 1 type host
    step emit
    step take performance
    step chooseleaf firstn -1 type host
    step emit
}

# end crush map
"""
        self._write_to_crushmap(string)


