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

"""Handles all requests to the physical service."""

from oslo.config import cfg
from vsm.db import base
from vsm.physical import rpcapi
from vsm.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

class API(base.Base):
    """Physical API that does updates via RPC to the PhysicalManager."""

    def __init__(self, **kwargs):
        self.physical_rpcapi = rpcapi.PhysicalAPI()
        super(API, self).__init__(**kwargs)

    def create(self, context, physical_info):
        """Use physical info to create a physical node."""
        return self.db.init_node_create(context, physical_info)
