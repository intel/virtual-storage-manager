#    Copyright 2014 Intel
#    All Rights Reserved
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

"""Client side of the scheduler RPC API."""
import logging
from oslo.config import cfg

from vsm.openstack.common import jsonutils
from vsm.openstack.common import rpc
import vsm.openstack.common.rpc.proxy

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

class SchedulerAPI(vsm.openstack.common.rpc.proxy.RpcProxy):
    """Client side of the scheduler RPC API"""

    BASE_RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        super(SchedulerAPI, self).__init__(
            topic = topic or CONF.scheduler_topic,
            default_version=self.BASE_RPC_API_VERSION)

    def ping(self, context, arg, timeout=None):
        arg_p = jsonutils.to_primitive(arg)
        msg = self.make_msg('ping', arg=arg_p)
        return self.call(context, msg, version='1.22', timeout=timeout)

    def test_service(self, ctxt, body=None):
        ret = self.call(ctxt, self.make_msg('test_service', body=body))
        return ret

    def create_storage_pool(self, ctxt, body=None):
        return self.call(ctxt, self.make_msg('create_storage_pool', body=body))

    def add_cache_tier(self, ctxt, body=None):
        return self.call(ctxt, self.make_msg('add_cache_tier', body=body))

    def remove_cache_tier(self, ctxt, body=None):
        return self.call(ctxt, self.make_msg('remove_cache_tier', body=body))

    def get_smart_info(self, ctxt, body=None):
        return self.call(ctxt, self.make_msg('get_smart_info', body=body))

    def list_storage_pool(self, ctxt):
        ret = self.call(ctxt, self.make_msg('list_storage_pool'))
        return ret

    def present_storage_pools(self, ctxt, body=None):
        ret = self.cast(ctxt, self.make_msg('present_storage_pools', body=body))
        return ret

    def get_storage_group_list(self, ctxt):
        ret = self.call(ctxt, self.make_msg('get_storage_group_list'))
        return ret

    def get_server_list(self, ctxt):
        ret = self.call(ctxt, self.make_msg('get_server_list'))
        return ret

    def add_servers(self, ctxt, body=None):
        #NOTE change this procedure to rpc.cast method()
        ret = self.cast(ctxt, self.make_msg('add_servers', body=body))
        return ret

    def remove_servers(self, ctxt, body=None):
        ret = self.cast(ctxt, self.make_msg('remove_servers', body=body))
        return ret

    def start_server(self, ctxt, body=None):
        ret = self.cast(ctxt, self.make_msg('start_server', body=body))
        return ret

    def stop_server(self, ctxt, body=None):
        ret = self.cast(ctxt, self.make_msg('stop_server', body=body))
        return ret

    def ceph_upgrade(self, ctxt, body=None):
        ret = self.cast(ctxt, self.make_msg('ceph_upgrade', body=body))
        return ret

    def get_cluster_list(self, ctxt):
        ret = self.call(ctxt, self.make_msg('get_cluster_list'))
        return ret

    def create_cluster(self, context, server_list):
        ret = self.cast(context,
                        self.make_msg('create_cluster',
                                      server_list=server_list))
        return ret

    def integrate_cluster(self, context, server_list):
        ret = self.cast(context,
                        self.make_msg('integrate_cluster',
                                      server_list=server_list))
        return ret

    def get_zone_list(self, ctxt):
        ret = self.call(ctxt, self.make_msg('get_zone_list'))
        return ret

    # TO_BE_CHANGED
    def create_zone(self, ctxt, attrs):
        ret = self.call(ctxt, self.make_msg('create_zone'), attrs=attrs)
        return ret

    def add_new_zone(self, ctxt, values):
        ret = self.call(ctxt, self.make_msg('add_new_zone', values=values))

    def osd_remove(self, ctxt, body):
        ret = self.call(ctxt, self.make_msg('osd_remove', osd_id=body), \
                        version='1.0', timeout=6000)
        return ret

    def osd_restart(self, ctxt, body):
        ret = self.call(ctxt, self.make_msg('osd_restart', osd_id=body), \
                        version='1.0', timeout=6000)
        return ret

    def osd_add(self, ctxt, body):
        ret = self.call(ctxt, self.make_msg('osd_add', osd_id=body), \
                        version='1.0', timeout=6000)
        return ret

    def osd_restore(self, ctxt, body):
        ret = self.call(ctxt, self.make_msg('osd_restore', osd_id=body), \
                        version='1.0', timeout=6000)
        return ret

    def osd_refresh(self, ctxt):
        ret = self.call(ctxt, self.make_msg('osd_refresh'),
                        version='1.0', timeout=6000)
        return ret

    def cluster_refresh(self, ctxt):
        ret = self.call(ctxt, self.make_msg('cluster_refresh'),
                        version='1.0', timeout=6000)
        return ret

    def health_status(self, context):
        ret = self.call(context,
                        self.make_msg('health_status'),
                        version='1.0',
                        timeout=6000)
        return ret

    def import_ceph_conf(self, context, cluster_id, ceph_conf_path):
        ret = self.call(context,
                        self.make_msg('import_ceph_conf',
                                      cluster_id=cluster_id, ceph_conf_path=ceph_conf_path))
        return ret

    def start_server(self, context, body=None):
        ret = self.call(context,
                        self.make_msg('start_server',
                                      body=body))
        return ret

    def stop_server(self, context, body=None):
        ret = self.call(context,
                        self.make_msg('stop_server',
                                      body=body))
        return ret

    def start_cluster(self, context, body=None):
        ret = self.call(context,
                        self.make_msg('start_cluster',
                                      body=body))
        return ret

    def stop_cluster(self, context, body=None):
        ret = self.call(context,
                        self.make_msg('stop_cluster',
                                      body=body))
        return ret

    def monitor_restart(self, ctxt, body):
        ret = self.call(ctxt, self.make_msg('monitor_restart', monitor_id=body), \
                        version='1.0', timeout=6000)
        return ret

    def get_ceph_health_list(self, ctxt, body=None):
        return self.call(ctxt, self.make_msg('get_ceph_health_list', body=body))

    def get_available_disks(self, ctxt, body=None):
        return self.call(ctxt, self.make_msg('get_available_disks', body=body))

    def add_new_disks_to_cluster(self, ctxt, body=None):
        return self.call(ctxt, self.make_msg('add_new_disks_to_cluster', body=body))

    def reconfig_diamond(self, ctxt, body=None):
        return self.cast(ctxt, self.make_msg('reconfig_diamond', body=body))
