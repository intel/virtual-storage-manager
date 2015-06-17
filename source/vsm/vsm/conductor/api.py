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

"""Handles all requests to the conductor service."""

from oslo.config import cfg

from vsm.conductor import manager
from vsm.conductor import rpcapi
from vsm import exception as exc
from vsm.openstack.common import log as logging
from vsm.openstack.common.rpc import common as rpc_common
from vsm import utils

conductor_opts = [
    cfg.StrOpt('manager',
               default='vsm.conductor.manager.ConductorManager',
               help='full class name for the Manager for conductor'),
]
conductor_group = cfg.OptGroup(name='conductor',
                               title='Conductor Options')
CONF = cfg.CONF
CONF.register_group(conductor_group)
CONF.register_opts(conductor_opts, conductor_group)

LOG = logging.getLogger(__name__)

class API(object):
    """Conductor API that does updates via RPC to the ConductorManager."""

    def __init__(self):
        self.conductor_rpcapi = rpcapi.ConductorAPI()

    def get_osd_num(self, context, storage_group_id):
        return self.conductor_rpcapi.get_osd_num(context, storage_group_id)

    def list_storage_pool(self, context):
        return self.conductor_rpcapi.list_storage_pool(context)

    def get_storage_group_list(self, context):
        return self.conductor_rpcapi.get_storage_group_list(context)

    def get_server_list(self, context):
        return self.conductor_rpcapi.get_server_list(context)

    def get_server(self, context, id):
        return self.conductor_rpcapi.get_server(context, id)

    def add_servers(self, context, attrs):
        return self.conductor_rpcapi.add_servers(context, attrs)

    def get_cluster_list(self, context):
        return self.conductor_rpcapi.get_cluster_list(context)

    def create_cluster(self, context, attrs):
        return self.conductor_rpcapi.get_server_list(context, attrs)

    def get_zone_list(self, context):
        return self.conductor_rpcapi.get_zone_list(context)

    def create_zone(self, context, values):
        return self.conductor_rpcapi.create_zone(context, values)

    def get_mapping(self, context):
        return self.conductor_rpcapi.get_mapping(context)

    def test_service(self, context):
        return self.conductor_rpcapi.test_service(context)

    def check_poolname(self, context, poolname):
        return self.conductor_rpcapi.check_poolname(context, poolname)

    def create_storage_pool(self, context, body):
        return self.conductor_rpcapi.create_storage_pool(context, body)

    def get_ruleset_id(self, context, storage_group_id):
        return self.conductor_rpcapi.get_ruleset_id(context, storage_group_id)

    def count_hosts_by_storage_group_id(self, context, storage_group_id):
        return self.conductor_rpcapi.count_hosts_by_storage_group_id(context, \
                                     storage_group_id)

    #def get_server_list(self, context):
    #    return self.conductor_rpcapi.get_server_list(context)

    #def get_service_by_host_and_topic(self, context, host, topic):
    #    return self.conductor_rpcapi.get_service_by_host_and_topic(context, host, topic)
################################<ly

    #init_node
    def init_node_get_by_id_and_type(self, context, id, type):
        return self.conductor_rpcapi.\
               init_node_get_by_id_and_type(context, id, type)

    def init_node_get_by_id(self, context, id):
        return self.conductor_rpcapi.init_node_get_by_id(context, id)

    def init_node_create(self, context, values):
        return self.conductor_rpcapi.\
               init_node_create(context, values)

    def init_node_get_by_primary_public_ip(self, context, primary_public_ip):
        return self.conductor_rpcapi.\
               init_node_get_by_primary_public_ip(context, primary_public_ip)

    def init_node_get_by_secondary_public_ip(self, context, \
                                             secondary_public_ip):
        return self.conductor_rpcapi.\
               init_node_get_by_secondary_public_ip(context, \
               secondary_public_ip)

    def init_node_get_by_cluster_ip(self, context, cluster_ip):
        return self.conductor_rpcapi.\
               init_node_get_by_cluster_ip(context, cluster_ip)

    def init_node_update(self, context, id, values):
        return self.conductor_rpcapi.init_node_update(context, id, values)

    def init_node_update_status_by_id(self, context, init_node_id, status):
        """Update init nodes info."""
        #TODO delete this function in the futhure.
        #We will not expose this function in WSGI-api.
        return self.conductor_rpcapi.init_node_update_status_by_id(context,
                                                                   init_node_id,
                                                                   status)
    #osd_state
    def osd_get(self, context, osd_id):
        return self.conductor_rpcapi.\
               osd_get(context, osd_id)

    def osd_delete(self, context, osd_id):
        return self.conductor_rpcapi.\
               osd_delete(context, osd_id)

    def osd_remove(self, context, osd_id):
        return self.conductor_rpcapi.\
               osd_remove(context, osd_id)

    def osd_state_get_all(self, context, limit=None, marker=None, sort_keys=None, sort_dir=None):
        return self.conductor_rpcapi.\
               osd_state_get_all(context, limit, marker, sort_keys, sort_dir)

    def osd_state_update_or_create(self, context, values, create=None):
        return self.conductor_rpcapi.\
               osd_state_update_or_create(context, values, create)

    def osd_state_create(self, context, values):
        result = self.osd_state_get_by_osd_name_and_service_id_and_cluster_id(\
                 context, values['osd_name'], values['service_id'],\
                 values['cluster_id'])
        if not result:
            result = self.osd_state_get_by_device_id_and_service_id_and_cluster_id(\
                 context, values['device_id'], values['service_id'],\
                 values['cluster_id'])
        if not result:
            return self.conductor_rpcapi.\
               osd_state_update_or_create(context, values, create=True)
        else:
            values['id'] = result['id']
            values['deleted'] = 0
            return self.conductor_rpcapi.\
                osd_state_update_or_create(context, values, create=False)

    def osd_state_count_by_init_node_id(self, context, init_node_id):
        return self.conductor_rpcapi.\
               osd_state_count_by_init_node_id(context, init_node_id)

    def osd_state_get_by_service_id_and_storage_group_id(self, context, \
                                        service_id, storage_group_id):
        return self.conductor_rpcapi.\
               osd_state_get_by_service_id_and_storage_group_id(context, \
               service_id, storage_group_id)

    def osd_state_get_by_osd_name_and_service_id_and_cluster_id(\
        self, context, osd_name, service_id, cluster_id):
        return self.conductor_rpcapi.\
               osd_state_get_by_osd_name_and_service_id_and_cluster_id(\
               context, osd_name, service_id, cluster_id)
    def osd_state_get_by_device_id_and_service_id_and_cluster_id(\
        self, context, device_id, service_id, cluster_id):
        return self.conductor_rpcapi.\
               osd_state_get_by_device_id_and_service_id_and_cluster_id(\
               context, device_id, service_id, cluster_id)
    #device
    def device_get_all(self, context):
        return self.conductor_rpcapi.device_get_all(context)

    def device_get_all_by_service_id(self, context, service_id):
        return self.conductor_rpcapi.device_get_all_by_service_id(context, \
               service_id)

    def device_get_distinct_storage_class_by_service_id(self, context, \
                                                        service_id):
        return self.conductor_rpcapi.\
               device_get_distinct_storage_class_by_service_id(context, \
                                                        service_id)

    def device_create(self, context, values):
        return self.conductor_rpcapi.device_create(context, values)

    def device_update(self, context, device_id, values):
        values['id'] = device_id
        return self.conductor_rpcapi.\
               device_update_or_create(context, values, create=False)

    def device_get_by_name_and_journal_and_service_id(self, context, \
                                                  name, journal, \
                                                  service_id):
        return self.conductor_rpcapi.\
               device_get_by_name_and_journal_and_service_id(context, name, \
                                                journal, service_id)

    #zone
    def zone_get_all(self, context):
        return self.conductor_rpcapi.zone_get_all(context)

    def zone_get_by_id(self, context, id):
        return self.conductor_rpcapi.zone_get_by_id(context, id)

    def zone_get_by_name(self, context, name):
        return self.conductor_rpcapi.zone_get_by_name(context, name)

    #storage_group
    def storage_group_get_all(self, context):
        return self.conductor_rpcapi.storage_group_get_all(context)

    def create_storage_group(self, context, attrs):
        return self.conductor_rpcapi.create_storage_group(context, attrs)

    #cluster
    def cluster_create(self, context, values):
        return self.conductor_rpcapi.cluster_create(context, values)

    def cluster_get_by_name(self, context, name):
        return self.conductor_rpcapi.cluster_get_by_name(context, name)

    #service
    def service_get_by_host_and_topic(self, context, host, topic):
        return self.conductor_rpcapi.service_get_by_host_and_topic(context, \
                                     host, topic)
    #ceph
    def host_storage_groups_devices(self, context, \
                                    init_node_id):
        return self.conductor_rpcapi.\
               host_storage_groups_devices(context, \
               init_node_id)

    def ceph_node_info(self, context, init_node_id):
        return self.conductor_rpcapi.\
               ceph_node_info(context, init_node_id)

    #pg
    def pg_get_all(self, context, limit, marker, sort_keys, sort_dir):
        return self.conductor_rpcapi.\
               pg_get_all(context, limit, marker, sort_keys, sort_dir)

    #rbd
    def rbd_get_all(self, context, limit, marker, sort_keys, sort_dir):
        return self.conductor_rpcapi.\
               rbd_get_all(context, limit, marker, sort_keys, sort_dir)

    #license_status
    def license_status_create(self, context, values):
        return self.conductor_rpcapi.\
                license_status_create(context, values)

    def license_status_get(self, context):
        return self.conductor_rpcapi.license_status_get(context)

    def license_status_update(self, context, value):
        return self.conductor_rpcapi.\
               license_status_update(context, value)

    #mds
    def mds_get_all(self, context):
        return self.conductor_rpcapi.\
               mds_get_all(context)

    def ceph_error(self, context):
        return self.conductor_rpcapi.\
               ceph_error(context)

    def zones_hosts_get_by_storage_group(self, context, storage_group):
        return self.conductor_rpcapi.\
               zones_hosts_get_by_storage_group(context, storage_group)

    def get_performance_metrics(self, context, search_opts):
        return self.conductor_rpcapi.get_performance_metrics(context, search_opts)

    def get_sum_performance_metrics(self, context, search_opts):
        return self.conductor_rpcapi.get_sum_performance_metrics(context, search_opts)

    def get_lantency(self, context, search_opts):
        return self.conductor_rpcapi.get_lantency(context, search_opts)
