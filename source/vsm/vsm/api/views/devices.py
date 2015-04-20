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
    _collection_name = "devices"

    def basic(self, request, device):
        #LOG.info("devices api view %s " % device)
        return {
            "device": {
                "id":device['id'],
                "name": device['name'],
                "path": device['path'],
                "journal": device['journal'],
                "device_type": device['device_type'],
                "state": device['state'],
                "journal_state": device['journal_state'],
                "total_capacity_kb": device['total_capacity_kb'],
                "avail_capacity_kb": device['avail_capacity_kb'],
                "used_capacity_kb": device['used_capacity_kb'],
            }
        }

    def index(self, request, devices):
        """Show a list of devices without many details."""
        return self._list_view(self.basic, request, devices)

    def _list_view(self, func, request, devices):
        """Provide a view for a list of devices."""
        device_list = [func(request, device)["device"] for device in devices]
        devices_dict = dict(devices=device_list)
        LOG.info("---devices_dict---%s"%devices_dict)
        return devices_dict

