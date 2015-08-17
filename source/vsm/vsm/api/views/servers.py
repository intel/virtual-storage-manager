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
    _collection_name = "servers"

    def basic(self, server):
        if not server['type']:
            server['type'] = "";
        return {
            "server": {
                "id": server["id"], 
                "host": server["host"], 
                "primary_public_ip": server["primary_public_ip"], 
                "secondary_public_ip": server["secondary_public_ip"], 
                "cluster_ip": server["cluster_ip"],
                "raw_ip":"192.168.1.3,192.168.2.3,192.168.3.3",
                "zone_id": server["zone_id"],
                "ceph_ver": server["ceph_ver"],
                "service_id": server["service_id"],
                "osds": server['data_drives_number'],
                "type": server['type'],
                "status": server['status']
            }
        }

    def index(self, servers):
        """Show a list of servers without many details."""
        return self._list_view(self.basic, servers)

    def _list_view(self, func, servers):
        """Provide a view for a list of servers."""
        server_list = [func(server)["server"] for server in servers]
        servers_dict = dict(servers=server_list)
        return servers_dict

