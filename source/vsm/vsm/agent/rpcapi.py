#    Copyright 2014 Intel
#    All rights reserved
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

"""Client side of the agent RPC API."""
import logging
from oslo.config import cfg

from vsm.openstack.common import jsonutils
from vsm.openstack.common import rpc
import vsm.openstack.common.rpc.proxy

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

class AgentAPI(vsm.openstack.common.rpc.proxy.RpcProxy):
    """Client side of the agent RPC API"""

    BASE_RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        super(AgentAPI, self).__init__(
            topic = topic or CONF.agent_topic,
            default_version=self.BASE_RPC_API_VERSION)

    def ping(self, context, arg, timeout=None):
        arg_p = jsonutils.to_primitive(arg)
        msg = self.make_msg('ping', arg=arg_p)
        return self.call(context, msg, version='1.0', timeout=timeout)

    def test_service(self, ctxt, topic, host=None):
        if host:
            topic = rpc.queue_get_for(ctxt, self.topic, host)
        ret = self.call(ctxt, self.make_msg('test_service'), topic, timeout=30, need_try=False)
        return ret

    def update_pool_info(self, ctxt, body=None):
        res = self.cast(ctxt, self.make_msg('update_pool_info', body=body))

    def update_recipe_info(self, ctxt, body=None):
        res = self.call(ctxt, self.make_msg('update_recipe_info', body=body))
        return res

    def present_storage_pools(self, context, body=None):
        return self.cast(context, self.make_msg('present_storage_pools', body=body))

    def revoke_storage_pool(self, context, id):
        return self.call(context, self.make_msg('revoke_storage_pool', id=id))

    def update_keyring_admin_from_db(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                    self.make_msg('update_keyring_admin_from_db'),
                    topic)

    def upload_keyring_admin_into_db(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                    self.make_msg('upload_keyring_admin_into_db'),
                topic, version='1.0', timeout=6000)

    def init_ceph(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context,
                         self.make_msg('init_ceph',
                                       body=body),
                         topic,
                         version='1.0', timeout=6000)

    def add_osd(self, context, host_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context,
                         self.make_msg('add_osd',
                                       host_id=host_id),
                         topic,
                         version='1.0', timeout=6000)

    def add_monitor(self, context, host_id, mon_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context,
                         self.make_msg('add_monitor',
                                       mon_id=mon_id,
                                       host_id=host_id),
                         topic,
                         version='1.0', timeout=6000)

    def remove_osd(self, context, host_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context,
                         self.make_msg('remove_osd',
                                       host_id=host_id),
                         topic,
                         version='1.0', timeout=6000)

    def remove_monitor(self, context, host_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context,
                         self.make_msg('remove_monitor',
                                       host_id=host_id),
                         topic,
                         version='1.0', timeout=6000)

    def remove_mds(self, context, host_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context,
                         self.make_msg('remove_mds',
                                       host_id=host_id),
                         topic,
                         version='1.0', timeout=6000)

    def add_mds(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context,
                         self.make_msg('add_mds'),
                         topic,
                         version='1.0', timeout=6000)

    def get_ceph_disk_list(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context,
                        self.make_msg('get_ceph_disk_list',),
                        topic, version='1.0', timeout=6000)

    def get_ceph_config(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context,
                        self.make_msg('get_ceph_config',),
                        topic, version='1.0', timeout=6000)

    def save_ceph_config(self, context, config, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                        self.make_msg('save_ceph_config', config=config),
                    topic, version='1.0', timeout=6000)

    def get_ceph_admin_keyring(self, context, host,):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                        self.make_msg('get_ceph_admin_keyring',),
                    topic, version='1.0', timeout=6000)

    def save_ceph_admin_keyring(self, context, keyring_str, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                         self.make_msg('save_ceph_admin_keyring',
                                      keyring_str=keyring_str),
                     topic, version='1.0', timeout=6000)

    def clean_ceph_data(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                         self.make_msg('clean_ceph_data'),
                         topic,
                         version='1.0', timeout=6000)

    def mount_disks(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                         self.make_msg('mount_disks'),
                         topic,
                         version='1.0', timeout=6000)

    def start_osd_daemon(self, context, number, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                         self.make_msg('start_osd_daemon',
                                       num=number),
                         topic,
                         version='1.0', timeout=6000)

    def get_ceph_health(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context,
                         self.make_msg('get_ceph_health'),
                         topic, version='1.0', timeout=6000)

    def get_ceph_health_list(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                         self.make_msg('get_ceph_health_list'),
                         topic, version='1.0', timeout=6000)

    def get_osds_total_num(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context, self.make_msg('get_osds_total_num'), topic,
                version='1.0', timeout=6000)
 
    def start_ceph(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        return self.call(context, self.make_msg('start_ceph'), topic,
                version='1.0', timeout=6000)

    def create_storage_pool(self, ctxt, body=None):
        return self.call(ctxt, self.make_msg('create_storage_pool', body=body))

    def get_pool_id_by_name(self, context, name, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                      self.make_msg('get_pool_id_by_name',
                                    name=name),
                      topic, version='1.0', timeout=6000)
        return res

    def set_crushmap(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                        self.make_msg('set_crushmap'),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def update_ssh_keys(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                        self.make_msg('update_ssh_keys'),
                        topic, version='1.0', timeout=6000)
        return res
    def get_smart_info(self, context, host, device):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                        self.make_msg('get_smart_info', device=device),
                        topic, version='1.0', timeout=6000)
        return res
    def create_crushmap(self, context, server_list, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                        self.make_msg('create_crushmap',
                                      server_list=server_list),
                        topic, version='1.0', timeout=6000)
        return res

    def refresh_osd_num(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.cast(context,
                        self.make_msg('refresh_osd_number'),
                        topic, version='1.0', timeout=6000)
        return res

    def add_new_zone(self, context, zone_name, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                        self.make_msg('add_new_zone',
                                        zone_name=zone_name),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def start_server(self, context, node_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                        self.make_msg('start_server',
                                       node_id=node_id),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def stop_server(self, context, node_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                        self.make_msg('stop_server',
                                       node_id=node_id),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def ceph_upgrade(self, context, node_id, host, key_url, pkg_url,restart):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                        self.make_msg('ceph_upgrade',node_id=node_id,key_url=key_url,pkg_url=pkg_url,restart=restart),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def osd_remove(self, context, osd_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        #self.test_service(context, topic)
        res = self.call(context,
                      self.make_msg('osd_remove',
                                    osd_id=osd_id),
                      topic, version='1.0', timeout=6000)
        return res

    def osd_restart(self, context, osd_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        #self.test_service(context, topic)
        res = self.call(context,
                      self.make_msg('osd_restart',
                                    osd_id=osd_id),
                      topic, version='1.0', timeout=6000)
        return res

    def osd_add(self, context, osd_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        #self.test_service(context, topic)
        res = self.call(context,
                      self.make_msg('osd_add',
                                    osd_id=osd_id),
                      topic, version='1.0', timeout=6000)
        return res

    def osd_restore(self, context, osd_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        #self.test_service(context, topic)
        res = self.call(context,
                      self.make_msg('osd_restore',
                                    osd_id=osd_id),
                      topic, version='1.0', timeout=6000)
        return res

    def osd_refresh(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('osd_refresh'),
                        topic, version='1.0', timeout=6000)
        return res

    def cluster_refresh(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('cluster_refresh'),
                        topic, version='1.0', timeout=6000)
        return res

    def integrate_cluster_update_status(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('integrate_cluster_update_status'),
                        topic, version='1.0', timeout=6000)
        return res

    def integrate_cluster_sync_osd_states(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('integrate_cluster_sync_osd_states'),
                        topic, version='1.0', timeout=6000)
        return res

    def integrate_cluster_from_ceph(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('integrate_cluster_from_ceph'),
                        topic, version='1.0', timeout=6000)
        return res

    def cluster_id(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                      self.make_msg('cluster_id'),
                  topic, version='1.0', timeout=6000)
        return res

    def update_osd_state(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.cast(context, self.make_msg('update_osd_state'), topic)

    def update_pool_state(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context, self.make_msg('update_pool_state'), topic)

    def update_mon_state(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.cast(context, self.make_msg('update_mon_health'), topic)

    def set_pool_pg_pgp_num(self, context, host, pool, pg_num, pgp_num):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.cast(context, self.make_msg('set_pool_pg_pgp_num',
                  pool=pool, pg_num=pg_num, pgp_num=pgp_num), topic)

    def update_all_status(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.cast(context, self.make_msg('update_all_status'), topic)

    def update_ceph_conf(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.cast(context, self.make_msg('update_ceph_conf'), topic)


    def start_monitor(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context, self.make_msg('start_monitor'), topic,
                        version='1.0', timeout=6000)

    def start_mds(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context, self.make_msg('start_mds'), topic,
                        version='1.0', timeout=6000)

    def start_osd(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context, self.make_msg('start_osd'), topic,
                        version='1.0', timeout=6000)

    def inital_ceph_osd_db_conf(self, context, server_list,ceph_conf_in_cluster_manifest,host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                         self.make_msg('inital_ceph_osd_db_conf',
                                       server_list=server_list,
                                       ceph_conf_in_cluster_manifest=ceph_conf_in_cluster_manifest),
                         topic,
                         version='1.0',
                         timeout=6000)

    def mkcephfs(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                         self.make_msg('mkcephfs'),
                         topic,
                         version='1.0',
                         timeout=6000)

    def stop_mds(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context, self.make_msg('stop_mds'), topic,
                        version='1.0', timeout=6000)

    def health_status(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context, self.make_msg('health_status'), topic)

    def write_monitor_keyring(self, context, monitor_keyring, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                         self.make_msg('write_monitor_keyring',
                                        monitor_keyring=monitor_keyring),
                         topic,
                         version='1.0', timeout=6000)

    def track_monitors(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('track_monitors'),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def create_keyring(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('create_keyring'),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def prepare_osds(self, context, server_list, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('prepare_osds',
                        server_list=server_list),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def add_cache_tier(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('add_cache_tier',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)

    def remove_cache_tier(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('remove_cache_tier',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)

    def start_cluster(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                        self.make_msg('start_cluster'),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def stop_cluster(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        self.test_service(context, topic)
        res = self.call(context,
                        self.make_msg('stop_cluster'),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def monitor_restart(self, context, monitor_num, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        #self.test_service(context, topic)
        res = self.call(context,
                      self.make_msg('monitor_restart',
                                    monitor_num=monitor_num),
                      topic, version='1.0', timeout=6000)
        return res

    def get_available_disks(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('get_available_disks'),
                        topic, version='1.0', timeout=6000)
        return res

    def add_new_disks_to_cluster(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('add_new_disks_to_cluster',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)

    def reconfig_diamond(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.cast(context,
                        self.make_msg('reconfig_diamond',
                                      body=body),
                        topic)

    def check_pre_existing_cluster(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('check_pre_existing_cluster',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def import_cluster(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('import_cluster',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def detect_cephconf(self, context, keyring, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('detect_cephconf',
                                      keyring=keyring),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def detect_crushmap(self, context, keyring, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('detect_crushmap',
                                      keyring=keyring),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def add_rule_to_crushmap(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('add_rule_to_crushmap',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def modify_rule_in_crushmap(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('modify_rule_in_crushmap',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def update_zones_from_crushmap_to_db(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('update_zones_from_crushmap_to_db',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def update_storage_groups_from_crushmap_to_db(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('update_storage_groups_from_crushmap_to_db',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def add_zone_to_crushmap_and_db(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('add_zone_to_crushmap_and_db',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def get_default_pg_num_by_storage_group(self, context, body, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('get_default_pg_num_by_storage_group',
                                      body=body),
                        topic,
                        version='1.0', timeout=6000)
        return res

    def rgw_create(self, context, name, host, keyring, log_file, rgw_frontends,
                   is_ssl, s3_user_uid, s3_user_display_name, s3_user_email,
                   swift_user_subuser, swift_user_access, swift_user_key_type):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context, self.make_msg('rgw_create',
                                               name=name,
                                               host=host,
                                               keyring=keyring,
                                               log_file=log_file,
                                               rgw_frontends=rgw_frontends,
                                               is_ssl=is_ssl,
                                               s3_user_uid=s3_user_uid,
                                               s3_user_display_name=s3_user_display_name,
                                               s3_user_email=s3_user_email,
                                               swift_user_subuser=swift_user_subuser,
                                               swift_user_access=swift_user_access,
                                               swift_user_key_type=swift_user_key_type),
                        topic, version='1.0', timeout=6000)
        return res