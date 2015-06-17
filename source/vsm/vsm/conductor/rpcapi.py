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

"""Client side of the conductor RPC API."""
import logging
from oslo.config import cfg

from vsm.openstack.common import jsonutils
from vsm.openstack.common import rpc
import vsm.openstack.common.rpc.proxy

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

class ConductorAPI(vsm.openstack.common.rpc.proxy.RpcProxy):
    """Client side of the conductor RPC API"""

    BASE_RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        super(ConductorAPI, self).__init__(
            topic = topic or CONF.conductor_topic,
            default_version=self.BASE_RPC_API_VERSION)

    def test_service(self, ctxt):
        ret = self.call(ctxt, self.make_msg('test_service'))
        return ret

    def get_osd_num(self, ctxt, group_id):
        ret = self.call(ctxt, self.make_msg('get_osd_num', group_id=group_id))
        return ret

    def list_storage_pool(self, ctxt):
        ret = self.call(ctxt, self.make_msg('list_storage_pool'))
        return ret

    def destroy_storage_pool(self, ctxt, pool_name):
        self.cast(ctxt, self.make_msg('destroy_storage_pool', pool_name=pool_name))

    def update_storage_pool(self, context, pool_id, values):
        return self.call(context, self.make_msg('update_storage_pool',
                                                pool_id=pool_id, values=values))

    def update_storage_pool_by_name(self, context, pool_name, cluster_id, values):
        return self.call(context, self.make_msg('update_storage_pool_by_name',
                                                pool_name=pool_name,
                                                cluster_id=cluster_id,
                                                values=values))

    def get_storage_group_list(self, ctxt):
        ret = self.call(ctxt, self.make_msg('get_storage_group_list'))
        return ret

    def get_server_list(self, ctxt):
        ret = self.call(ctxt, self.make_msg('get_server_list'))
        return ret

    def get_server(self, ctxt, id):
        ret = self.call(ctxt, self.make_msg('get_server', id=id))
        return ret

    def add_servers(self, ctxt, attrs):
        ret = self.call(ctxt, self.make_msg('add_servers'), attrs=attrs)
        return ret

    def get_cluster_list(self, ctxt):
        ret = self.call(ctxt, self.make_msg('cluster_get_all'))
        return ret

    def create_cluster(self, ctxt, attrs):
        ret = self.call(ctxt, self.make_msg('create_cluster'), attrs=attrs)
        return ret

    def get_zone_list(self, ctxt):
        ret = self.call(ctxt, self.make_msg('get_zone_list'))
        return ret

    def create_zone(self, ctxt, values):
        ret = self.call(ctxt, self.make_msg('create_zone', values=values))
        return ret

    def get_mapping(self, ctxt):
        ret = self.call(ctxt, self.make_msg('get_mapping'))
        return ret

    def check_poolname(self, context, poolname):
        ret = self.call(context, self.make_msg('check_poolname', \
                        poolname=poolname))
        return ret

    def create_storage_pool(self, context, body):
        ret = self.call(context, self.make_msg('create_storage_pool', \
                        body=body))
        return ret

    def get_ruleset_id(self, ctxt, group_id):
        ret = self.call(ctxt, self.make_msg('get_ruleset_id', group_id=group_id))
        return ret

    def count_hosts_by_storage_group_id(self, context, storage_group_id):
        ret = self.call(context, self.make_msg('count_hosts_by_storage_group_id', \
                        storage_group_id=storage_group_id))
        return ret

#    def get_server_list(self, ctxt):
#        ret = self.call(ctxt, self.make_msg('get_server_list'))
#        return ret
#
#    def get_service_by_host_and_topic(self, ctxt, host, topic):
#        ret = self.call(ctxt, self.make_msg('get_service_by_host_and_topic', host=host, topic=topic))
#        return ret

#############################################ly>

    def init_node_get_by_host(self, ctxt, host):
        """Get init node ref by host name"""
        return self.call(ctxt,
                         self.make_msg('init_node_get_by_host',
                         host=host))

    def init_node_get_by_cluster_id(self, ctxt, cluster_id):
        """Get init node ref by host name"""
        return self.call(ctxt,
                         self.make_msg('init_node_get_by_cluster_id',
                         cluster_id=cluster_id))

    def init_node_get_cluster_nodes(self, ctxt, init_node_id):
        """Get nodes in the same cluster."""
        return self.call(ctxt,
                         self.make_msg('init_node_get_cluster_nodes',
                         init_node_id=init_node_id))

    #init_node
    def init_node_get_by_id_and_type(self, ctxt, id, type):
        ret = self.call(ctxt, self.make_msg('init_node_get_by_id_and_type',\
                        id=id, type=type))
        return ret

    def init_node_get_by_id(self, ctxt, id):
        ret = self.call(ctxt, self.make_msg('init_node_get_by_id', id=id))
        return ret

    def init_node_create(self, context, values):
        return  self.call(context, self.make_msg('init_node_create', \
                          values=values))

    def init_node_get_by_primary_public_ip(self, context, primary_public_ip):
        return self.call(context, self.\
                         make_msg('init_node_get_by_primary_public_ip',\
                         primary_public_ip=primary_public_ip))

    def init_node_get_by_secondary_public_ip(self, context, \
                                             secondary_public_ip):
        return self.call(context, self.\
                         make_msg('init_node_get_by_secondary_public_ip',\
                         secondary_public_ip=secondary_public_ip))

    def init_node_get_by_cluster_ip(self, context, cluster_ip):
        return self.call(context, self.make_msg('init_node_get_by_cluster_ip',\
                         cluster_ip=cluster_ip))

    def init_node_update(self, context, id, values):
        return self.call(context, self.make_msg('init_node_update', id=id, \
                         values=values))

    def init_node_update_status_by_id(self, context, init_node_id, status):
        """Update init node by id, change status."""
        return self.call(context,
                         self.make_msg('init_node_update_status_by_id',
                         init_node_id=init_node_id,
                         status=status))

    #osd_state
    def osd_get(self, context, osd_id):
        return self.call(context, self.make_msg('osd_get', osd_id=osd_id))

    def osd_delete(self, context, osd_id):
        return self.call(context, self.make_msg('osd_delete', osd_id=osd_id))

    def osd_remove(self, context, osd_id):
        return self.call(context, self.make_msg('osd_remove', osd_id=osd_id))

    def osd_state_get_all(self, context, limit, marker, sort_keys, sort_dir):
        return self.call(context, self.make_msg('osd_state_get_all', \
                         limit=limit, marker=marker, sort_keys=sort_keys, \
                         sort_dir=sort_dir))

    def osd_state_create(self, context, values):
        return self.call(context, self.make_msg('osd_state_create', \
                         values=values))

    def osd_state_update(self, context, values):
        return self.call(context, self.make_msg('osd_state_update', \
                         values=values))

    def osd_state_update_or_create(self, context, values, create=None):
        return self.call(context, self.make_msg('osd_state_update_or_create', \
                         values=values, create=create), need_try=False)

    def osd_state_count_by_init_node_id(self, context, init_node_id):
        return self.call(context, self.\
                         make_msg('osd_state_count_by_init_node_id',\
                         init_node_id=init_node_id))

    def osd_state_get_by_service_id_and_storage_group_id(self, context, \
                                                         service_id, \
                                                         storage_group_id):
        return self.\
               call(context, \
               self.\
               make_msg('osd_state_get_by_service_id_and_storage_group_id', \
               service_id=service_id, storage_group_id=storage_group_id))

    def osd_state_get_by_service_id(self, context, service_id):
        return self.\
               call(context, \
               self.\
               make_msg('osd_state_get_by_service_id', \
               service_id=service_id))

    def osd_state_get_by_osd_name_and_service_id_and_cluster_id(self, \
        context, osd_name, service_id, cluster_id):
        return self.call(context, self.\
        make_msg('osd_state_get_by_osd_name_and_service_id_and_cluster_id',\
               osd_name=osd_name, service_id=service_id, \
               cluster_id=cluster_id))

    def osd_state_get_by_device_id_and_service_id_and_cluster_id(self, \
        context, device_id, service_id, cluster_id):
        return self.call(context, self.\
        make_msg('osd_state_get_by_device_id_and_service_id_and_cluster_id',\
               device_id=device_id, service_id=service_id, \
               cluster_id=cluster_id))

    #device
    def device_get_all(self, context):
        return self.call(context, self.make_msg('device_get_all'))

    def device_get_by_hostname(self, context, hostname):
        return self.call(context, self.make_msg('device_get_by_hostname', \
                         hostname=hostname))

    def device_create(self, context, values):
        return self.call(context, \
                         self.make_msg('device_create', values=values))

    def device_update_or_create(self, context, values, create=None):
        return self.call(context, self.make_msg('device_update_or_create', \
                         values=values, create=create))

    def device_get_all_by_service_id(self, context, service_id):
        return self.call(context, \
                         self.make_msg('device_get_all_by_service_id',\
                         service_id=service_id))

    def device_get_distinct_storage_class_by_service_id(self, context,\
                                                        service_id):
        return self.\
               call(context, self.\
               make_msg('device_get_distinct_storage_class_by_service_id',\
                        service_id=service_id))

    def device_get_by_name_and_journal_and_service_id(self, context, \
                                                  name, journal, \
                                                  service_id):
        return self.\
               call(context, self.\
               make_msg('device_get_by_name_and_journal_and_service_id', \
                        name=name, journal=journal, service_id=service_id))

    #storage_group
    def storage_group_get_all(self, context):
        return self.call(context, self.make_msg('storage_group_get_all'))

    def create_storage_group(self, context, values):
        return self.call(context, self.make_msg('create_storage_group', \
                         values=values))

    #zone
    def zone_get_all(self, context):
        return self.call(context, self.make_msg('zone_get_all'))

    def zone_get_by_id(self, context, id):
        return self.call(context, self.make_msg('zone_get_by_id', id=id))

    def zone_get_by_name(self, context, name):
        return self.call(context, self.make_msg('zone_get_by_name',
                         name=name))

    #cluster
    def cluster_create(self, context, values):
        return self.call(context, self.make_msg('cluster_create', 
                                                values=values))

    def cluster_update(self, context, cluster_id, values):
        return self.call(context, self.make_msg('cluster_update',
                                                cluster_id=cluster_id,
                                                values=values))

    def cluster_get_by_name(self, context, name):
        return self.call(context, self.make_msg('cluster_get_by_name',
                                                name=name))

    def cluster_info_dict_get_by_id(self, context, cluster_id):
        return self.call(context,
                         self.make_msg('cluster_info_dict_get_by_id',
                                       cluster_id=cluster_id))

    #service
    def service_get_by_host_and_topic(self, context, host, topic):
        return self.call(context, \
                         self.make_msg('service_get_by_host_and_topic',
                         host=host, topic=topic))

    #ceph
    def host_storage_groups_devices(self, context, \
                                    init_node_id):
        return self.call(context, \
                         self.make_msg('host_storage_groups_devices',
                         init_node_id=init_node_id))

    def ceph_node_info(self, context, init_node_id):
        return self.call(context, \
                         self.make_msg('ceph_node_info', \
                         init_node_id=init_node_id))

    #pg
    def pg_get_all(self, context, limit, marker, sort_keys, sort_dir):
        return self.call(context, \
                         self.make_msg('pg_get_all',
                                       limit=limit, marker=marker,
                                       sort_keys=sort_keys,
                                       sort_dir=sort_dir))

    #suggestion:you'd better not use this api! 
    #If the count of pgs is too large, it may blocks up the net.
    def pg_update_or_create(self, context, values):
        return self.call(context, \
                         self.make_msg('pg_update_or_create',
                         values=values))

    #rbd
    def rbd_get_all(self, context, limit, marker, sort_keys, sort_dir):
        return self.call(context, \
                         self.make_msg('rbd_get_all',
				       limit=limit, marker=marker,
					sort_keys=sort_keys, sort_dir=sort_dir))

    #license_status
    def license_status_create(self, context, values):
        return self.call(context,
                         self.make_msg('license_status_create',
                                       values=values))

    def license_status_get(self, context):
        return self.call(context,
                         self.make_msg('license_status_get'))

    def license_status_update(self, context, value):
        return self.call(context,
                         self.make_msg('license_status_update',
                                       value=value))

    #mds
    def mds_get_all(self, context):
        return self.call(context, \
                         self.make_msg('mds_get_all'))

    def ceph_error(self, context):
        return self.call(context, \
                         self.make_msg('ceph_error'))

    def zones_hosts_get_by_storage_group(self, context, storage_group):
        return self.call(context, \
                         self.make_msg('zones_hosts_get_by_storage_group', 
                                        storage_group=storage_group))


    def get_performance_metrics(self, context, search_opts):
        return self.call(context,self.make_msg('get_performance_metrics', \
                               search_opts=search_opts))

    def get_sum_performance_metrics(self, context, search_opts):
        return self.call(context,self.make_msg('get_sum_performance_metrics', \
                               search_opts=search_opts))

    def get_lantency(self, context, search_opts):
        return self.call(context,self.make_msg('get_lantency', \
                               search_opts=search_opts))