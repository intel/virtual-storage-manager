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
        LOG.info("DEBUG in update_pool_info of rpcapi")
        res = self.cast(ctxt, self.make_msg('update_pool_info', body=body))

    def update_recipe_info(self, ctxt, body=None):
        LOG.info("DEBUG in update_recipe_info of rpcapi")
        res = self.call(ctxt, self.make_msg('update_recipe_info', body=body))
        return res

    def present_storage_pools(self, context, body=None):
        return self.call(context, self.make_msg('present_storage_pools', body=body))

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

    def osd_restore(self, context, osd_id, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        #self.test_service(context, topic)
        res = self.call(context,
                      self.make_msg('osd_restore',
                                    osd_id=osd_id),
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
        return self.call(context, self.make_msg('start_monitor'), topic)

    def start_mds(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context, self.make_msg('start_mds'), topic)

    def start_osd(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context, self.make_msg('start_osd'), topic)

    def inital_ceph_osd_db_conf(self, context, server_list, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                         self.make_msg('inital_ceph_osd_db_conf',
                                       server_list=server_list),
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
        return self.call(context, self.make_msg('stop_mds'), topic)

    def health_status(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context, self.make_msg('health_status'), topic)

    def write_monitor_keyring(self, context, monitor_keyring, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        return self.call(context,
                         self.make_msg('write_monitor_keyring',
                                        monitor_keyring=monitor_keyring),
                         topic)

    def track_monitors(self, context, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('track_monitors'),
                        topic)
        return res

    def prepare_osds(self, context, server_list, host):
        topic = rpc.queue_get_for(context, self.topic, host)
        res = self.call(context,
                        self.make_msg('prepare_osds',
                        server_list=server_list),
                        topic)
        return res
