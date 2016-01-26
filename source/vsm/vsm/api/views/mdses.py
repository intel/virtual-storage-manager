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
    _collection_name = "mdses"

    def basic(self, request, mds):
        LOG.info("mdses api view %s " % mds)
        _mds = {
            "mds": {
                "id": mds['id'],
                "name": mds['name'],
                "gid": mds['gid'],
                "state": mds['state'],
                "address": mds['address']
            }
        }
        _mds['mds']['updated_at'] = time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(mds['updated_at'], "%Y-%m-%dT%H:%M:%S.000000"))
        return _mds

    def _detail(self, request, mds):
        LOG.info("mdses api detail view %s " % mds)
        _mds = {
            "mds": {
                "id": mds['id'],
                "name": mds['name'],
                "gid": mds['gid'],
                "state": mds['state'],
                "address": mds['address']
            }
        }
        try:
            _mds['mds']['updated_at'] = time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(mds['updated_at'], "%Y-%m-%dT%H:%M:%S.000000"))
        except:
            _mds['mds']['updated_at'] = ""
        return _mds

    def detail(self, request, mdses):
        return self._list_view(self._detail, request, mdses)

    def index(self, request, mdses):
        """Show a list of mdses without many details."""
        return self._list_view(self.basic, request, mdses)

    def _list_view(self, func, request, mdses):
        """Provide a view for a list of mdses."""
        mds_list = [func(request, mds)["mds"] for mds in mdses]
        mdses_dict = dict(mdses=mds_list)
        return mdses_dict

