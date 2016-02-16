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
OSDs interface.
"""

import urllib
from vsmclient import base


class Osd(base.Resource):
    """
    A osd stores data, handles data replication, recovery,
    backfilling, rebalancing and provides some monitor information
    to Ceph monitors by checking other Ceph OSD Daemons for a heartbeat.
    """
    def __repr__(self):
        try:
            return "<OSD: %s>" % self.id
        except AttributeError:
            return "<OSD: summary>"

    def delete(self):
        """Delete this osd."""
        self.manager.delete(self)

class OsdManager(base.ManagerWithFind):
    """
    Manage :class:`OSD` resources.
    """
    resource_class = Osd

    def get(self, osd_id):
        """
        Get a osd.

        :param osd_id: The ID of the osd.
        :rtype: :class:`OSD`
        """
        return self._get("/osds/%s" % osd_id, "osd")

    def list(self, detailed=False, search_opts=None, paginate_opts=None):
        """
        Get a list of all osds.

        :rtype: list of :class:`OSD`
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
        if detailed == 'detail_filter_and_sort':
            detail = "/detail_filter_and_sort"
        elif detailed:
            detail = "/detail"

        ret = self._list("/osds%s%s" % (detail, query_string),
                          "osds")
        return ret

    def restart(self, osd):
        self._action('restart', osd)

    def remove(self, osd):
        self._action('remove', osd)

    def add_new_disks_to_cluster(self, body):

        """
        :param body:
         body={'server_id':server_id,
                        'osdinfo':[{'storage_group_id':
                                    "weight":
                                    "jounal":
                                    "data":
                }]}
        :return:
        """
        url = '/osds/add_new_disks_to_cluster'
        return self.api.client.post(url, body=body)

    def add_batch_new_disks_to_cluster(self, body):
        """

        :param context:
        :param body: {"disks":[
                                {'server_id':'1','osdinfo':[{'storage_group_id':
                                                            "weight":
                                                            "jounal":
                                                            "data":},{}]},
                                {'server_id':'2','osdinfo':[{'storage_group_id':
                                                            "weight":
                                                            "jounal":
                                                            "data":},{}]},
                            ]
                    }
        :return:
        """
        url = '/osds/add_batch_new_disks_to_cluster'
        return self.api.client.post(url, body=body)

    def delete(self, osd):
        self._delete("/osds/%s" % base.getid(osd))

    def restore(self, osd):
        self._action('restore', osd)

    def refresh(self):
        url = "/osds/refresh"
        return self.api.client.post(url)

    def summary(self):
        """
        summary
        """
        url = "/osds/summary"
        return self._get(url, 'osd-summary')

    def _action(self, action, osd, info=None, **kwargs):
        """
        Perform a osd "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/osds/%s/action' % base.getid(osd)
        return self.api.client.post(url, body=body)

