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

"""Handles all requests to the scheduler service."""

from oslo.config import cfg

from vsm.scheduler import manager
from vsm.scheduler import rpcapi
from vsm import exception as exc
from vsm.openstack.common import log as logging
from vsm.openstack.common.rpc import common as rpc_common
from vsm import utils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

class API(object):
    """Scheduler API that does updates via RPC to the SchedulerManager."""

    def __init__(self):
        self.scheduler_rpcapi = rpcapi.SchedulerAPI()

    def test_service(self, context, body=None):
        LOG.info(' scheduler/api.py test_service()')
        return self.scheduler_rpcapi.test_service(context, body)

    def create_storage_pool(self, context, body=None):
        LOG.info('DEBUG scheduler/api.py create_storageool()')
        return self.scheduler_rpcapi.create_storage_pool(context, body)

    def list_storage_pool(self, context):
        LOG.info('scheduler/api.py list_storageool()')
        return self.scheduler_rpcapi.list_storage_pool(context)

    def present_storage_pools(self, context, body=None):
        LOG.info('scheduler/api.py present_storage_pools()')
        return self.scheduler_rpcapi.present_storage_pools(context, body)

    def get_storage_group_list(self, context):
        LOG.info('scheduler/api.py get_storage_group_list()')
        return self.scheduler_rpcapi.get_storage_group_list(context)

    def get_server_list(self, context):
        LOG.info('scheduler/api.py get_server_list()')
        return self.scheduler_rpcapi.get_server_list(context)

    def add_servers(self, context, body=None):
        LOG.info('in scheduler/api.py add_servers %s ' % body)
        return self.scheduler_rpcapi.add_servers(context, body)

    def remove_servers(self, context, body=None):
        LOG.info('in scheduler/api.py remove_servers %s ' % body)
        return self.scheduler_rpcapi.remove_servers(context, body)

    def get_cluster_list(self, context):
        LOG.info('in scheduler/api.py get_cluster_list')
        return self.scheduler_rpcapi.get_server_list(context)

    def create_cluster(self, context, server_list):
        LOG.info('in scheduler/api.py create_cluster')
        return self.scheduler_rpcapi.create_cluster(context, server_list)

    def get_zone_list(self, context):
        LOG.info('in scheduler/api.py get_zone_list')
        return self.scheduler_rpcapi.get_server_list(context)

    def add_new_zone(self, context, values):
        LOG.info('In scheduler/api.py add_new_zone')
        return self.scheduler_rpcapi.add_new_zone(context, values)

    def create_zone(self, context, attrs):
        LOG.info('in scheduler/api.py create_zone')
        return self.scheduler_rpcapi.get_server_list(context)

    def osd_remove(self, context, body=None):
        LOG.info('in scheduler/api.py osd_remove')
        return self.scheduler_rpcapi.osd_remove(context, body)

    def osd_restart(self, context, body=None):
        LOG.info('in scheduler/api.py osd_restart')
        return self.scheduler_rpcapi.osd_restart(context, body)

    def osd_restore(self, context, body=None):
        LOG.info('in scheduler/api.py osd_restore')
        return self.scheduler_rpcapi.osd_restore(context, body)

    def health_status(self, context):
        return self.scheduler_rpcapi.health_status(context)
