# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel.
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
Conductor Service
"""

import json
from oslo.config import cfg
import datetime
from vsm import context
from vsm import db
from vsm import exception
from vsm import flags
from vsm import manager
from vsm.openstack.common import excutils
from vsm.openstack.common import importutils
from vsm.openstack.common import log as logging
from vsm.openstack.common.notifier import api as notifier
from vsm.openstack.common import timeutils

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class ConductorManager(manager.Manager):
    """Chooses a host to create storages."""

    RPC_API_VERSION = '1.2'

    def __init__(self, service_name=None, *args, **kwargs):
        #if not scheduler_driver:
        #    scheduler_driver = FLAGS.scheduler_driver
        #self.driver = importutils.import_object(scheduler_driver)
        super(ConductorManager, self).__init__(*args, **kwargs)

    def init_host(self):
        LOG.info('init_host in manager ')

    def test_service(self, context):
        LOG.info(' test_service in conductor')
        return {'key': 'test_server_in_conductor'}

    def check_poolname(self, context, poolname):
        pool_list = db.pool_get_all(context)
        if pool_list:
            for pool in pool_list:
                if pool['name'] == poolname:
                    return 1
        return 0

    def create_storage_pool(self, context, body):
        #TO BE DONE
        body['cluster_id'] = db.cluster_get_all(context)[0]['id']#1
        res = db.pool_create(context, body)
        return res

    def update_storage_pool(self, context, pool_id, values):
        return db.pool_update(context, pool_id, values)

    def update_storage_pool_by_name(self, context, pool_name, cluster_id, values):
        return db.pool_update_by_name(context, pool_name, cluster_id, values)

    def get_osd_num(self, context, group_id):
        osds = db.osd_get_all(context)

        osd_num = 0
        for osd in osds:
            if osd['deleted'] == False and \
            str(osd['storage_group_id']) == str(group_id):
                osd_num = osd_num + 1

        return osd_num

    def list_storage_pool(self, context):
        LOG.info('list_storage_pool in conductor manager')

        pool_list = db.pool_get_all(context)
        pool_list_dict = {}
        if pool_list:
            for pool in pool_list:
                pool_list_dict[pool['id']] = pool

        return pool_list_dict

    def destroy_storage_pool(self, context, pool_name):
        if pool_name:
            db.pool_destroy(context, pool_name)

    def get_storage_group_list(self, context):
        LOG.info('get_storage_group_list in conductor manager')

        storage_group_list = db.storage_group_get_all(context)
        storage_group_list = [x for x in storage_group_list if x.status == "IN"]
        osds = db.osd_get_all(context)

        group_list = {}
        if storage_group_list:
            for group in storage_group_list:
                osd_num=0
                for osd in osds:
                    if osd['storage_group_id'] == group['id']:
                        osd_num = osd_num + 1
                if osd_num > 0:
                    group_list[group['id']] = group['name']
        return group_list

    def get_server_list(self, context):
        LOG.info('get_server_list in conductor manager')
        server_list = db.init_node_get_all(context)
        ret = self._set_error(context)
        for ser in server_list:
            if ret:
                ser['status'] = ret
        return server_list

    def _set_error(self, context, cluster_id = None):
        if cluster_id:
            summary = db.summary_get_by_cluster_id_and_type(context, cluster_id, 'cluster')
        else:
            summary = db.summary_get_by_type_first(context, 'cluster')
        #summary = db.summary_get_by_cluster_id_and_type(context, 1, 'cluster')
        if summary:
            sum_data = json.loads(summary['summary_data'])
            h_list = sum_data.get('health_list')
            if len(h_list) > 0:
                if h_list[0].find('ERROR') != -1:
                    return h_list[0]
        return None

    def ceph_error(self, context):
        return self._set_error(context)

    def get_cluster_list(self, context):
        LOG.info('get_server_list in conductor manager')
        cluster_list = db.init_node_get_all(context)
        ret = self._set_error(context)
        for ser in cluster_list:
            if ret:
                ser['status'] = 'unavailable'
        return cluster_list

    def get_server(self, context, id):
        LOG.info('get_server_list in conductor manager')
        server = db.init_node_get(context, id)
        ret = self._set_error(context)
        if ret:
            server['status'] = 'unavailable'

        LOG.info("CEPH_LOG log server %s" % server)
        return server

    def get_zone_list(self, context):
        LOG.info('get_zone_list in conductor manager')
        zone_list = db.zone_get_all(context)
        LOG.info("CEPH_LOG log server_list %s" % zone_list)
        return zone_list

    def get_mapping(self, context):
        LOG.info('get_mapping in conductor manager')
        storage_group_list = db.storage_group_get_all(context)
        mapping = {}
        if storage_group_list:
            for group in storage_group_list:
                mapping[group['rule_id']] = group['friendly_name']
        return mapping

    def get_ruleset_id(self, context, group_id):
        LOG.info("Get ruleset id via storage_group id.")
        storage_group = db.storage_group_get(context, group_id)
        return storage_group['rule_id']

    def count_hosts_by_storage_group_id(self, context, storage_group_id):
        return db.osd_state_count_service_id_by_storage_group_id(context, \
           storage_group_id)

    def init_node_get_by_host(self, context, host):
        """Get init node by host name."""
        return db.init_node_get_by_host(context, host)

    def init_node_get_by_cluster_id(self, context, cluster_id):
        """Get init node by cluster id."""
        return db.init_node_get_by_cluster_id(context, cluster_id)

    def init_node_get_cluster_nodes(self, context, init_node_id):
        """Get cluster nodes by id"""
        return db.init_node_get_cluster_nodes(context, init_node_id)

    #init_node
    def init_node_get_by_id_and_type(self, context, id, type):
        #LOG.info("get init node by id and type")
        init_node = db.init_node_get_by_id_and_type(context, id, type)
        return init_node

    def init_node_get_by_id(self, context, id):
        #LOG.info("get init node by id")
        init_node = db.init_node_get_by_id(context, id)
        return init_node

    def init_node_create(self, context, values):
        return db.init_node_create(context, values)

    def init_node_update(self, context, id, values):
        return db.init_node_update(context, id, values)

    def init_node_get_by_primary_public_ip(self, context, primary_public_ip):
        return db.init_node_get_by_primary_public_ip(context, \
                                                     primary_public_ip)

    def init_node_get_by_secondary_public_ip(self, context, \
                                             secondary_public_ip):
        return db.init_node_get_by_secondary_public_ip(context, \
                                                       secondary_public_ip)

    def init_node_get_by_cluster_ip(self, context, cluster_ip):
        return db.init_node_get_by_cluster_ip(context, cluster_ip)

    def init_node_update_status_by_id(self,
                                      context,
                                      init_node_id,
                                      status):
        """ConductorManager update the status of init node."""
        return db.init_node_update_status_by_id(context,
                                                init_node_id,
                                                status)

    #osd_state
    def osd_get(self, context, osd_id):
        return db.osd_get(context, osd_id)

    def osd_delete(self, context, osd_id):
        return db.osd_delete(context, osd_id)

    def osd_remove(self, context, osd_id):
        return db.osd_remove(context, osd_id)

    def osd_state_get_all(self,
                          context,
                          limit=None,
                          marker=None,
                          sort_keys=None,
                          sort_dir=None):
        all_osd = db.osd_state_get_all(context,
                                       limit,
                                       marker,
                                       sort_keys,
                                       sort_dir)
        return all_osd

    def osd_state_get_by_name(self, context, name):
        return db.osd_state_get_by_name(context, name)

    def osd_state_create(self, context, values):
        LOG.info('ADD_OSD values = %s' % values)
        result = db.osd_state_get_by_osd_name_and_service_id_and_cluster_id(\
                 context, values['osd_name'], values['service_id'],\
                 values['cluster_id'])
        if not result:
            result = db.osd_state_get_by_device_id_and_service_id_and_cluster_id(\
                 context, values['device_id'], values['service_id'],\
                 values['cluster_id'])
        LOG.info('ADD_OSD result = %s' % result)

        if not result:
            LOG.info('ADD_OSD result is None')
            return db.\
               osd_state_create(context, values)
        else:
            LOG.info('ADD_OSD result is ok')
            values['id'] = result['id']
            values['deleted'] = 0
            return db.\
                osd_state_update(context, values['id'], values)

    def osd_state_update(self, context, values):
        #LOG.info("osd_state_update")
        osd_ref = db.osd_state_get_by_name(context, values['osd_name'])
        if osd_ref:
            osd_state = db.osd_state_update(context, osd_ref['id'], values)
            return osd_state

    def osd_state_update_or_create(self, context, values, create=None):
        #LOG.info("osd_state_update_or_create")
        osd_ref = db.osd_state_get_by_name(context, values['osd_name'])
        if not osd_ref:
            osd_ref = db.osd_state_get_by_device_id_and_service_id_and_cluster_id(\
                 context, values['device_id'], values['service_id'],\
                 values['cluster_id'])
        if osd_ref:
            osd_state = db.osd_state_update(context, osd_ref['id'], values)
            return osd_state
        else:
            create = True

        if create is None:
            osd_state = db.osd_state_update_or_create(context, values)
        elif create == True:
            osd_state = db.osd_state_create(context, values)
        else:
            #LOG.info("osd values:%s" % values)
            osd_state_ref = db.osd_state_get_by_name(context, values['osd_name'])
            if osd_state_ref:
                values['id'] = osd_state_ref.id
                osd_state = db.osd_state_update(context,
			                      values['id'],
					      values)
            else:
                return None 
        return osd_state

    def osd_state_count_by_init_node_id(self, context, init_node_id):
        return db.osd_state_count_by_init_node_id(context, init_node_id)

    def osd_state_get_by_service_id_and_storage_group_id(self, context, \
                                                         service_id, \
                                                         storage_group_id):
        return db.osd_state_get_by_service_id_and_storage_group_id(\
                  context, service_id, storage_group_id)

    def osd_state_get_by_service_id(self, context, service_id):
        return db.osd_state_get_by_service_id(context, service_id)

    def osd_state_get_by_osd_name_and_service_id_and_cluster_id(self, \
            context, osd_name, service_id, cluster_id):
        return db.osd_state_get_by_osd_name_and_service_id_and_cluster_id(\
            context, osd_name, service_id, cluster_id)

    def osd_state_get_by_device_id_and_service_id_and_cluster_id(self, \
            context, device_id, service_id, cluster_id):
        return db.osd_state_get_by_device_id_and_service_id_and_cluster_id(\
            context, device_id, service_id, cluster_id)
    #device
    def device_get_all(self, context):
        error = self._set_error(context)
        all_devices = db.device_get_all(context)
        if not error:
            return all_devices

        for dev in all_devices:
            dev['state'] = error
            dev['journal_state'] = error

        return all_devices

    def device_get_by_hostname(self, context, hostname):
        init_node = db.init_node_get_by_hostname(context, hostname)
        if init_node:
            service_id = init_node['service_id']
            device_list = db.device_get_by_service_id(context, service_id)
            if device_list:
                return device_list
        else:
            return None

    def device_create(self, context, values):
        return db.device_create(context, values)

    def device_update_or_create(self, context, values, create=None):
        if create is None:
            device = db.device_update_or_create(context, values)
        elif create is True:
            device = db.device_create(context, values)
        else:
            device = db.device_update(context,\
                                      values['id'],\
                                      values)
        return device

    def device_get_all_by_service_id(self, context, service_id):
        return db.device_get_all_by_service_id(context, service_id)

    def device_get_distinct_storage_class_by_service_id(self, context,\
                                                        service_id):
        return db.device_get_distinct_storage_class_by_service_id(context,\
                                                                 service_id)

    def device_get_by_name_and_journal_and_service_id(self, context, \
                                                  name, journal, service_id):
        return db.device_get_by_name_and_journal_and_service_id(context, name, \
                                                journal, service_id)

    #storage_group
    def storage_group_get_all(self, context):
        return db.storage_group_get_all(context)

    def create_storage_group(self, context, values):
        if values is None:
            LOG.warn("Error: Empty values")
            try:
                raise exception.GetNoneError
            except exception.GetNoneError, e:
                LOG.error("%s:%s", e.code, e.message)
            return False

        res = db.storage_group_get_all(context)
        name_list = []
        for item in res:
            name_list.append(item['name'])

        if values['name'] not in name_list:
            db.storage_group_create(context, values)
        else:
            LOG.info('Warnning: name exists in table %s' % values['name'])
            return False

        return True

    #zone
    def create_zone(self, context, values=None):
        if values is None:
            LOG.warn("Error: Empty values")
            try:
                raise exception.GetNoneError
            except exception.GetNoneError, e:
                LOG.error("%s:%s", e.code, e.message)
            return False

        res = db.zone_get_all(context)
        zone_list = []
        for item in res:
            zone_list.append(item['name'])

        if values['name'] not in zone_list:
            db.zone_create(context, values)
        else:
            LOG.info('Warnning: zone exists in table %s' % values['name'])
            return True

        return True

    def zone_get_all(self, context):
        return db.zone_get_all(context)

    def zone_get_by_id(self, context, id):
        return db.zone_get_by_id(context, id)

    def zone_get_by_name(self, context, name):
        return db.zone_get_by_name(context, name)

    #cluster
    def cluster_create(self, context, values):
        return db.cluster_create(context, values)

    def cluster_update(self, context, cluster_id, values):
        return db.cluster_update(context, cluster_id, values)

    def cluster_get_by_name(self, context, name):
        return db.cluster_get_by_name(context, name)

    def cluster_get_all(self, context):
        return db.cluster_get_all(context)

    def cluster_info_dict_get_by_id(self, context, cluster_id):
        return db.cluster_info_dict_get_by_id(context, cluster_id)

    #service
    def service_get_by_host_and_topic(self, context, host, topic):
        return db.service_get_by_host_and_topic(context, host, topic)

    #ceph
    def host_devices_by_init_node_id(self,
                                     context,
                                     init_node_id):
        init_node = db.init_node_get_by_id(context, init_node_id)
        #LOG.info("host_devices:init_node:%s", init_node)
        zone = db.zone_get_by_id(context, init_node['zone_id'])
        devices = db.device_get_all_by_service_id(context,
                                                  init_node['service_id'])
        file_system = init_node.cluster.file_system
        #osd_heartbeat_interval=init_node.cluster.osd_heartbeat_interval
        #osd_heartbeat_grace=init_node.cluster.osd_heartbeat_grace

        lst = []
        for device in devices:
            d = {}
            d['host'] = init_node['host']
            d['cluster_id'] = init_node['cluster_id']
            d['file_system'] = file_system
            d['primary_public_ip'] = init_node['primary_public_ip']
            d['secondary_public_ip'] = init_node['secondary_public_ip']
            d['cluster_ip'] = init_node['cluster_ip']
            d['data_drives_number'] = init_node['data_drives_number']
            d['dev_name'] = device['name']
            d['dev_journal'] = device['journal']
            d['dev_id'] = device['id']
            d['service_id'] = device['service_id']
            d['storage_class'] = device['device_type']
            d['zone_id'] = init_node['zone_id']
            d['zone'] = zone['name']
            lst.append(d)

        return lst

    def host_storage_groups_devices(self,
                                    context,
                                    init_node_id):
        # TODO all code refered is used as type = 'storage'
        # What type means?
        # Need to put the implementation into DB or manager.
        LOG.info(' conductor api:host_storage_groups_devices()')
        lst = self.host_devices_by_init_node_id(context, \
               init_node_id)

        storage_group_list = db.storage_group_get_all(context)

        for item in lst:
            for storage_group in storage_group_list:
                if storage_group['storage_class'] == item['storage_class']:
                    item['storage_group_id'] = storage_group['id']
                    # TODO should we use storage_group_name instead?
                    item['storage_group'] = storage_group['name']
                    item['storage_group_name'] = storage_group['name']
        return lst

    def ceph_node_info(self, context, init_node_id):
        init_node = db.init_node_get_by_id(context, init_node_id)
        zone = db.zone_get_by_id(context, init_node['zone_id'])
        storage_class_list = db.\
                             device_get_distinct_storage_class_by_service_id(\
                             context, init_node['service_id'])
        #LOG.info('storage_class_list:%s', storage_class_list)
        storage_group_list = db.storage_group_get_all(context)
        #LOG.info('storage_group_list:%s', storage_group_list)
        list = []
        for storage_class in storage_class_list:
            dict = {}
            for storage_group in storage_group_list:
                if storage_class == storage_group['storage_class']:
                    dict['storage_group_id'] = storage_group['id']
                    dict['storage_group_name'] = storage_group['name']
                    break
            list.append(dict)
        #LOG.info('list:%s', list)
        final_list = []
        for item in list:
            osd_state_list = db.\
                             osd_state_get_by_service_id_and_storage_group_id(  \
                             context, init_node['service_id'], \
                             item['storage_group_id'])
            if not osd_state_list:
                continue
            #LOG.info('osd_state_list:%s', osd_state_list)
            for osd_state in osd_state_list:
                final_dict = {}
                final_dict['osd_state_id'] = osd_state['id']
                final_dict['osd_state_name'] = osd_state['osd_name']
                final_dict['storage_group_name'] = item['storage_group_name']
                final_dict['host'] = init_node['host']
                final_dict['zone'] = zone['name']
                final_list.append(final_dict)
        return final_list

    #pg
    def pg_get_all(self, context, limit, marker, sort_keys, sort_dir):
        return db.pg_get_all(context, limit, marker, sort_keys, sort_dir)

    def pg_update_or_create(self, context, values):
        pg_ref = db.pg_get_by_pgid(context, values['pgid'])
        if pg_ref:
            pg = db.pg_update(context, pg_ref['id'], values)
        else:
            pg = db.pg_create(context, values)
        return pg

    #rbd
    def rbd_get_all(self, context, limit, marker, sort_keys, sort_dir):
        return db.rbd_get_all(context, limit, marker, sort_keys, sort_dir)

    def license_status_create(self, context, values):
        return db.license_status_create(context, values)

    def license_status_get(self, context):
        return db.license_status_get(context)

    def license_status_update(self, context, value):
        return db.license_status_update(context, value)

    #mds
    def mds_get_all(self, context):
        return db.mds_get_all(context)

    
    def zones_hosts_get_by_storage_group(self, context, storage_group):
        osds = db.osd_state_get_all(context)
        host_list = []
        zone_list = []
        for osd in osds:
            if storage_group == osd['storage_group']['name']:
                if osd['zone']['name'] not in zone_list:
                    zone_list.append(osd['zone']['name'])
                if osd['service']['host'] not in host_list:
                    host_list.append(osd['service']['host']) 
        return zone_list, host_list

    def get_performance_metrics(self, context, search_opts):
        return db.get_performance_metrics(context, search_opts=search_opts)

    def get_sum_performance_metrics(self, context, search_opts):
        return db.get_sum_performance_metrics(context, search_opts=search_opts)

    def get_lantency(self, context, search_opts):
        return db.get_lantency(context, search_opts=search_opts)
