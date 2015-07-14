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
    _collection_name = "clusters"

    def basic(self, cluster):
        return {
            "cluster": {
                "id":1, 
                "name": cluster['name'],
                "file_system": "",
                "journal_size": "",
                "size": "",
                "management_network": "",
                "ceph_public_network": "1",
                "cluster_network":"14",
                "primary_public_ip_netmask":"",
                "scecondary_public_ip_netmask": "",
                "cluster_ip_netmask": "",
            }
        }

    def index(self, clusters):
        """Show a list of servers without many details."""
        return self._list_view(self.basic, clusters)

    def _list_view(self, func, clusters):
        """Provide a view for a list of servers."""
        cluster_list = [func(cluster)["cluster"] for cluster in clusters]
        clusters_dict = dict(clusters=cluster_list)
        return clusters_dict

