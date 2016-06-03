# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Inc.
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

from vsm.api import common
import logging

LOG = logging.getLogger(__name__)

class ViewBuilder(common.ViewBuilder):
    _collection_name = "poolusages"

    def basic(self, poolusage):
        if not poolusage.get('id', ""):
            poolusage['id'] = ""
            return poolusage
        return {
            "poolusage": {
                "id": poolusage.get("id", 0),
                "pool_id": poolusage.get("pool_id", ""),
                "vsmapp_id": poolusage.get("vsmapp_id", ""),
                "cinder_volume_host": poolusage.get("cinder_volume_host", ""),
                "as_glance_store_pool": poolusage.get("as_glance_store_pool", ""),
                "attach_status": poolusage.get("attach_status", ""),
                "attach_at": poolusage.get("attach_at", "")
            }
        }

    def index(self, poolusages):
        """Show a list of poolusages without many details."""
        return self._list_view(self.basic, poolusages)

    def _list_view(self, func, poolusages):
        """Provide a view for a list of poolusages."""
        node_list = [func(poolusage)["poolusage"] for poolusage in poolusages]
        nodes_dict = dict(poolusages=node_list)
        return nodes_dict
