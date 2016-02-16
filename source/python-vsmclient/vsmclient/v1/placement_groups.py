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
Placement Groups interface.
"""

import urllib
from vsmclient import base


class PlacementGroup(base.Resource):
    """A placement group aggregates objects within a pool."""
    def __repr__(self):
        try:
            return "<PlacementGroup: %s>" % self.id
        except AttributeError:
            return "<PG: summary>"

class PlacementGroupsManager(base.ManagerWithFind):
    """
    Manage :class:`PlacementGroup` resources.
    """
    resource_class = PlacementGroup

    def get(self, placement_group_id):
        """
        Get a placement_group.

        :param placement_group_id: The ID of the placement_group.
        :rtype: :class:`PlacementGroup`
        """
        return self._get("/placement_groups/%s" % placement_group_id, "placement_group")

    def list(self, detailed=False, search_opts=None, paginate_opts=None):
        """
        Get a list of all placement_groups.

        :rtype: list of :class:`PlacementGroup`
        """
        if search_opts is None:
            search_opts = {}
        
        if paginate_opts is None:
            paginate_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val
        
        for opt, val in paginate_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"

        ret = self._list("/placement_groups%s%s" % (detail, query_string),
                          "placement_groups")
        return ret

    def summary(self):
        """
        summary
        """
        url = "/placement_groups/summary"
        return self._get(url, 'placement_group-summary')

    def _action(self, action, placement_group, info=None, **kwargs):
        """
        Perform a placement_group "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/placement_groups/%s/action' % base.getid(placement_group)
        return self.api.client.post(url, body=body)

