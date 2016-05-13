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
    _collection_name = "rbd_pools"

    def basic(self, request, rbd_pool):
        LOG.info("rbd_pools api view %s " % rbd_pool)
        rbd = {
            "rbd_pool": {
                "id": rbd_pool['id'],
                "pool": rbd_pool['pool'],
                "image_name": rbd_pool['image'],
                "size": rbd_pool['size'],
                "objects": rbd_pool['objects'],
                "order": rbd_pool['order'],
                "format": rbd_pool['format'],
            }
        }
        rbd['rbd_pool']['updated_at'] = time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(rbd_pool['updated_at'], "%Y-%m-%dT%H:%M:%S.000000"))
        return rbd

    def _detail(self, request, rbd_pool):
        LOG.info("rbd_pools api detail view %s " % rbd_pool)
        rbd = {
            "rbd_pool": {
                "id": rbd_pool['id'],
                "pool": rbd_pool['pool'],
                "image_name": rbd_pool['image'],
                "size": rbd_pool['size'],
                "objects": rbd_pool['objects'],
                "order": rbd_pool['order'],
                "format": rbd_pool['format'],
            }
        }
        try:
            rbd['rbd_pool']['updated_at'] = time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(rbd_pool['updated_at'], "%Y-%m-%dT%H:%M:%S.000000"))
        except:
            rbd['rbd_pool']['updated_at'] = time.strftime("%Y-%m-%d %H:%M:%S", time.strptime(rbd_pool['created_at'], "%Y-%m-%dT%H:%M:%S.000000"))
        return rbd

    def detail(self, request, rbd_pools):
        return self._list_view(self._detail, request, rbd_pools)

    def index(self, request, rbd_pools):
        """Show a list of rbd_pools without many details."""
        return self._list_view(self.basic, request, rbd_pools)

    def _list_view(self, func, request, rbd_pools):
        """Provide a view for a list of rbd_pools."""
        rbd_pool_list = [func(request, rbd_pool)["rbd_pool"] for rbd_pool in rbd_pools]
        rbd_pools_dict = dict(rbd_pools=rbd_pool_list)
        return rbd_pools_dict

