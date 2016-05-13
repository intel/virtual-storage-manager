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
MDSes interface.
"""

import urllib
from vsmclient import base


class Mds(base.Resource):
    """A mds stores metadata on behalf of the Ceph Filesystem."""
    def __repr__(self):
        return "<MDS: %s>" % self.id

    def delete(self):
        """Delete this mds."""
        self.manager.delete(self)

class MdsesManager(base.ManagerWithFind):
    """
    Manage :class:`MDS` resources.
    """
    resource_class = Mds

    def get(self, mds_id):
        """
        Get a mds.

        :param mds_id: The ID of the mds.
        :rtype: :class:`MDS`
        """
        return self._get("/mdses/%s" % mds_id, "mds")

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all mdses.

        :rtype: list of :class:`MDS`
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

        ret = self._list("/mdses%s%s" % (detail, query_string),
                          "mdses")
        return ret

    def restart(self, mds):
        self._action('restart', mds)

    def remove(self, mds):
        self._action('remove', mds)

    def delete(self, mds):
        self._delete("/mdses/%s" % base.getid(mds))

    def restore(self, mds):
        self._action('restore', mds)

    def summary(self):
        """
        summary
        """
        url = "/mdses/summary"
        return self._get(url, 'mds-summary')

    def _action(self, action, mds, info=None, **kwargs):
        """
        Perform a mds "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/mdses/%s/action' % base.getid(mds)
        return self.api.client.post(url, body=body)

