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
    _collection_name = "agents"

    def basic(self, agents):
        if not agents.get('host', ""):
            agents['host'] = ""
            return agents
        return {
            "agents": {
                "id": agents.get("id", ""),
                "host": agents.get("host", ""),
                "primary_public_ip": agents.get("primary_public_ip", ""),
                "secondary_public_ip": agents.get("secondary_public_ip", ""),
                "cluster_ip": agents.get("cluster_ip", ""),
                "cluster_id": agents.get("cluster_id", ""),
                "data_drives_number": agents.get('data_drives_number', ""),
                "id_rsa_pub": agents.get('id_rsa_pub', ""),
                "raw_ip": agents.get('raw_ip', ""),
                "zone_id": agents.get("zone_id", ""),
                "type": agents.get('type', ""),
                "status": agents.get('status', ""),
                "service_id": agents.get('service_id', "")
            }
        }

    def index(self, agentss):
        """Show a list of agentss without many details."""
        return self._list_view(self.basic, agentss)

    def _list_view(self, func, agentss):
        """Provide a view for a list of agentss."""
        agents_list = [func(agents)["agents"] for agents in agentss]
        agentss_dict = dict(agentss=agents_list)
        return agentss_dict
