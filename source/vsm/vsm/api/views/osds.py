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
from vsm import db
import time

LOG = logging.getLogger(__name__)

class ViewBuilder(common.ViewBuilder):
    _collection_name = "osds"

    def __init__(self):
        self._host = ''

    def basic(self, request, osd):
        LOG.info("osds api view %s " % osd)
        return {
            "osd": {
                "id":osd['id'],
                "osd_name": osd['osd_name'],
                "state": osd['state'],
                "operation_status": osd['operation_status'],
                "weight": osd['weight'],
                "device_id": osd['device_id'],
                "service_id": osd['service_id'],
                "updated_at": osd['updated_at'],
            }
        }

    def _detail(self, request, osd):
        LOG.info("osds api detail view %s " % osd)
        _osd = {
            "osd": {
                "id": osd['id'],
                "osd_name": osd['osd_name'],
                "state": osd.get('state', ''),
                "operation_status": osd.get('operation_status', ''),
                "weight": osd.get('weight', 0.0),
                #? "crush_weight": osd['crush_weight'],
                "device_id": osd['device_id'],
                "service_id": osd['service_id'],
                "service": osd['service'],
                "storage_group": osd['storage_group'],
                "zone": self._get_zone(request, osd),
                "device": osd['device'],
            }
        }
        try:
            _osd['osd']['updated_at'] = time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(osd['updated_at'], "%Y-%m-%dT%H:%M:%S.000000"))
        except:
            _osd['osd']['updated_at'] = ""

        return _osd

    def _get_zone(self, req, osd):
        """get zone name from server name"""
        zone = ''
        context = req.environ["vsm.context"]
        host = self._get_server(osd)
        if not host:
            return zone

        node = db.init_node_get_by_host(context=context, host=host)
        if node and node.zone:
            zone = node.zone.name

        return zone

    def _get_server(self, osd):
        if self._host:
            return self._host

        if osd and osd.get('service'):
            server = osd['service']['host']

        return server

    def detail(self, request, osds):
        return self._list_view(self._detail, request, osds)

    def index(self, request, osds):
        """Show a list of osds without many details."""
        return self._list_view(self.basic, request, osds)

    def _list_view(self, func, request, osds):
        """Provide a view for a list of osds."""
        osd_list = [func(request, osd)["osd"] for osd in osds]
        osds_dict = dict(osds=osd_list)
        return osds_dict

