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
    _collection_name = "appnodes"

    def basic(self, appnode):
        if not appnode.get('id', ""):
            appnode['id'] = ""
            return appnode
        return {
            "appnode": {
                "id": appnode.get("id", 0),
                # "ip": appnode.get("ip", ""),
                "os_tenant_name": appnode.get("os_tenant_name", ""),
                "os_username": appnode.get("os_username", ""),
                "os_password": appnode.get("os_password", ""),
                "os_auth_url": appnode.get("os_auth_url", ""),
                "os_region_name": appnode.get("os_region_name", ""),
                "uuid": appnode.get("uuid", ""),
                "ssh_user": appnode.get("ssh_user", ""),
                "vsmapp_id": appnode.get("vsmapp_id", ""),
                "ssh_status": appnode.get("ssh_status", ""),
                "log_info": appnode.get("log_info", "")
            }
        }

    def index(self, appnodes):
        """Show a list of appnodes without many details."""
        return self._list_view(self.basic, appnodes)

    def _list_view(self, func, appnodes):
        """Provide a view for a list of appnodes."""
        node_list = [func(appnode)["appnode"] for appnode in appnodes]
        nodes_dict = dict(appnodes=node_list)
        return nodes_dict
