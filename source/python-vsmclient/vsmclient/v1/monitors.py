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
Monitors interface.
"""

import urllib
from vsmclient import base


class Monitor(base.Resource):
    """
    A monitor maintain maps of the cluster state, including the
    monitor map, the OSD map, the PG map, and the CRUSH map.
    """
    def __repr__(self):
        return "<Monitor: %s>" % self.id

class MonitorsManager(base.ManagerWithFind):
    """
    Manage :class:`Monitor` resources.
    """
    resource_class = Monitor

    def get(self, monitor_id):
        """
        Get a monitor.

        :param monitor_id: The ID of the monitor.
        :rtype: :class:`Monitor`
        """
        return self._get("/monitors/%s" % monitor_id, "monitor")

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all monitors.

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

    def summary(self):
        """
        summary
        """
        url = "/monitors/summary"
        return self._get(url, 'monitor-summary')

    def restart(self, mon):
        self._action('restart', mon)

    def _action(self, action, monitor, info=None, **kwargs):
        """
        Perform a monitor "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/monitors/%s/action' % base.getid(monitor)
        return self.api.client.post(url, body=body)

