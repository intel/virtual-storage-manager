#
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
Monitors interface (1.1 extension).
"""

import urllib
from vsmclient import base

class Monitor(base.Resource):
    def __repr__(self):
        try:
            return "<MON: %s>" % self.id
        except AttributeError:
            return "<MON: Summary>"

    def delete(self):
        """Delete this mon."""
        self.manager.delete(self)

    def update(self, **kwargs):
        """Update the display_name or display_description for this mds."""
        self.manager.update(self, **kwargs)

class MonitorsManager(base.ManagerWithFind):
    """
    Manage :class:`Monitor` resources.
    """
    resource_class = Monitor

    def get(self, mon_id):
        """
        Get a mon.

        :param mon_id: The ID of the monitor.
        :rtype: :class:`Monitor`
        """
        return self._get("/monitors/%s" % mon_id, "monitor")

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all mons.

        :rtype: list of :class:`Monitor`
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

        ret = self._list("/monitors%s%s" % (detail, query_string),
                         "monitors")
        return ret

    def delete(self, mon):
        self._delete("/monitors/%s" % base.getid(mon))

    def summary(self):
        """
        summary
        """
        url = "/monitors/summary"
        return self._get(url, 'monitor-summary')
