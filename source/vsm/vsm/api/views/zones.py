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
    _collection_name = "zones"

    def basic(self, zone):
        #LOG.info("CEPH_LOG zone api view %s " % zone)
        return {
            "zone": {
                "id":zone['id'], 
                "name": zone["name"], 
            }
        }

    def index(self, zones):
        """Show a list of servers without many details."""
        return self._list_view(self.basic, zones)

    def _list_view(self, func, zones):
        """Provide a view for a list of servers."""
        zone_list = [func(zone)["zone"] for zone in zones]
        zones_dict = dict(zones=zone_list)
        return zones_dict

