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
import time

LOG = logging.getLogger(__name__)

class ViewBuilder(common.ViewBuilder):
    _collection_name = "monitors"

    def basic(self, mon):
        LOG.info("mon api view %s " % mon)
        return {
            "monitor": {
                "id": mon['id'],
                "name": mon['name'],
                "address": mon.get('address'),
                "health": mon.get('health'),
                "details": mon.get('details'),
            }
        }

    def show(self, mon):
        LOG.info("mon api view %s " % mon)
        _mon = {
            "monitor": {
                "id": mon['id'],
                "name": mon['name'],
                "address": mon.get('address'),
                "health": mon.get('health'),
                "details": mon.get('details'),
                "skew": float(mon.get('skew')),
                "latency": float(mon.get('latency')),
                "kb_total": mon.get('kb_total'),
                "kb_used": mon.get('kb_used'),
                "kb_avail": mon.get('kb_avail'),
                "avail_percent": mon.get('avail_percent')
            }
        }

        try:
            _mon['monitor']['updated_at'] = mon.get('updated_at').strftime("%Y-%m-%d %H:%M:%S")
        except:
            _mon['monitor']['updated_at'] = ""

        return _mon

    def index(self, mons):
        """Show a list of mons without many details."""
        return self._list_view(self.basic, mons)

    def detail(self, mons):
        return self._list_view(self.show, mons)

    def _list_view(self, func, mons):
        """Provide a view for a list of mons."""
        mon_list = [func(mon)["monitor"] for mon in mons]
        mons_dict = dict(monitors=mon_list)
        return mons_dict

