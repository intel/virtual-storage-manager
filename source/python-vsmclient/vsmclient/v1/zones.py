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
Zone interface.
"""

import urllib
from vsmclient import base
import logging


class Zone(base.Resource):
    """"""
    def __repr__(self):
        return "<Zone: %s>" % self.id

    def delete(self):
        """Delete this zone."""
        self.manager.delete(self)

    def update(self, **kwargs):
        """"""
        self.manager.update(self, **kwargs)

class ZoneManager(base.ManagerWithFind):
    """
    Manage :class:`Zone` resources.
    """
    resource_class = Zone

    def create(self, body):
               
        """
        Create a zone.
        """

        #body = {'zone': {'name': name
        #                   }}
        return self._create('/zones', body, 'zone')

    def get(self, zone_id):
        """
        Get a zone.

        :param zone_id: The ID of the zone to delete.
        :rtype: :class:`Zone`
        """
        return self._get("/zones/%s" % zone_id, "zone")

    def osd_locations_choices(self):
        """
        :rtype: :class:`Zone`
        """
        resp,body = self.api.client.get("/zones/osd_locations_choices")
        return body

    def get_zone_not_in_crush_list(self):
        """
        :rtype: :class:`Zone`
        """
        resp,body = self.api.client.get("/zones/get_zone_not_in_crush_list")
        return body

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all zones.

        :rtype: list of :class:`Zone`
        """
        #print ' comes to list'
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

        ret = self._list("/zones%s%s" % (detail, query_string),
                          "zones")
        return ret

    def delete(self, zone):
        """
        Delete a zone.

        :param zone: The :class:`Zone` to delete.
        """
        self._delete("/zones/%s" % base.getid(zone))

    def update(self, zone, **kwargs):
        """

        :param vsm: The :class:`Zone` to delete.
        """
        if not kwargs:
            return

        body = {"zone": kwargs}

        self._update("/zones/%s" % base.getid(zone), body)

    def _action(self, action, zone, info=None, **kwargs):
        """
        Perform a zone "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/zones/%s/action' % base.getid(zone)
        return self.api.client.post(url, body=body)

    def add_zone_to_crushmap_and_db(self,body):
        url = '/zones/add_zone_to_crushmap_and_db'
        return self.api.client.post(url, body=body)
