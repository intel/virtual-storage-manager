#  Copyright 2014 Intel Corporation, All Rights Reserved.
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

"""
StoragePools interface.
"""

import urllib
from vsmclient import base


class StoragePool(base.Resource):
    """"""
    def __repr__(self):
        return "<StoragePool: %s>" % self.id

    def delete(self):
        """Delete this storage pool."""
        self.manager.delete(self)

class StoragePoolManager(base.ManagerWithFind):
    """
    Manage :class:`StoragePool` resources.
    """
    resource_class = StoragePool

    def get(self, osd_id):
        """
        Get a osd.

        :param osd_id: The ID of the osd.
        :rtype: :class:`StoragePool`
        """
        return self._get("/storage_pools/%s" % osd_id, "pool")

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all storage_pools.

        :rtype: list of :class:`StoragePool`
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"

        ret = self._list("/storage_pools%s%s" % (detail, query_string),
                          "pool")
        return ret

    def add_cache_tier(self, cache_tier_body):
        url = '/storage_pools/add_cache_tier'
        resp, body = self.api.client.post(url, body=cache_tier_body)

    def remove_cache_tier(self, cache_tier_body):
        url = '/storage_pools/remove_cache_tier'
        resp, body = self.api.client.post(url, body=cache_tier_body)

    def restart(self, osd):
        self._action('restart', osd)

    def remove(self, osd):
        self._action('remove', osd)

    def delete(self, osd):
        self._delete("/storage_pools/%s" % base.getid(osd))

    def ec_profiles(self):
        url = '/storage_pools/get_ec_profile_list'
        resp, body = self.api.client.get(url)
        return body['ec_profiles']

    def _action(self, action, osd, info=None, **kwargs):
        """
        Perform a osd "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/storage_pools/%s/action' % base.getid(osd)
        return self.api.client.post(url, body=body)

