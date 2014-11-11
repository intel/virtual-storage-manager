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

"""Handles all requests to the agent service."""

from oslo.config import cfg

from vsm.agent import manager
from vsm.agent import rpcapi
from vsm import exception as exc
from vsm.openstack.common import log as logging
from vsm.openstack.common.rpc import common as rpc_common
from vsm import utils

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

class API(object):
    """Agent API that does updates via RPC to the AgentManager."""

    def __init__(self):
        self.agent_rpcapi = rpcapi.AgentAPI()

    def test_service(self, context):
        return self.agent_rpcapi.test_service(context)

    def present_storage_pools(self, context, body=None):
        LOG.debug('agent/api.py present_storage_pools()')
        return self.agent_rpcapi.present_storage_pools(context, body)

    def add_new_zone(self, context, zone_name, host):
        return self.agent_rpcapi.add_new_zone(context, zone_name, host)
