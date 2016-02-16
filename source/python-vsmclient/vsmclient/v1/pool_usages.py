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
Storage Pool Usage Interface.
"""

from vsmclient import base
import urllib


class PoolUsage(base.Resource):
    """"""
    def __repr__(self):
        return "<Pool Usage: %s>" % self.id

    def update(self, **kwargs):
        """update attach_status and time"""
        self.manager.update(self, **kwargs)

    def delete(self):
        """Delete this usage."""
        self.manager.delete(self)

class PoolUsageManager(base.ManagerWithFind):
    """
    Manage :class:`PoolUsage` resources.
    """
    resource_class = PoolUsage

    def create(self, pools=None):

        """
        Create pool usages.
        Param: a list of pool id and cinder_volume_host.
        """
        if not isinstance(pools, list):
            pool_list = list()
            pool_list.append(pools)
        else:
            pool_list = pools

        body = {'poolusages':  pool_list}
        return self._create('/poolusages', body, 'poolusages')

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all pool usages.
        :rtype: list of :class:`PoolUsage`
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

        ret = self._list("/poolusages%s%s" % (detail, query_string),
                          "poolusages")
        return ret

    def delete(self, poolusage):
        """
        Delete an pool usage.

        :param poolusage: The :class:`PoolUsage` to delete.
        """
        self._delete("/poolusages/%s" % base.getid(poolusage))

    def update(self, poolusage, **kargs):
        """
        Update the attach_status and time for a set of pool usages.

        """
        if not kargs:
            return

        body = {"poolusages": kargs}
        self._update("/poolusages/%s" % base.getid(poolusage), body)
