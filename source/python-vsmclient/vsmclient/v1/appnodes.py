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
Appnodes interface.
"""

from vsmclient import base
import urllib


class AppNode(base.Resource):
    """An appnode connects to openstack cinder."""
    def __repr__(self):
        return "<App Node: %s>" % self.id

    def update(self, **kwargs):
        """update ssh_status and log_info"""
        self.manager.update(self, **kwargs)

    def delete(self):
        """Delete this appnode."""
        self.manager.delete(self)

class AppNodeManager(base.ManagerWithFind):
    """
    Manage :class:`AppNode` resources.
    """
    resource_class = AppNode

    def create(self, auth_openstack):

        """
        Create a list of  app nodes.
        """
        #validate ip_list
        # if not isinstance(ips, list):
        #     ip_list = list()
        #     ip_list.append(ips)
        # else:
        #     ip_list = ips

        body = {'appnodes':  auth_openstack}
        return self._create('/appnodes', body, 'appnodes')

    def get(self, appnode_id):
        """
        Get details of an appnode.
        """
        return self._get("/appnodes/%s" % appnode_id, "appnode")

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all appnodes.
        :rtype: list of :class:`AppNode`
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

        ret = self._list("/appnodes%s%s" % (detail, query_string),
                          "appnodes")
        return ret

    def delete(self, appnode):
        """
        Delete an app node.

        :param appnode: The :class:`AppNode` to delete.
        """
        self._delete("/appnodes/%s" % base.getid(appnode))

    def update(self, appnode, appnode_info):
        """
        Update the ssh_status or log_info for an appnode.

        """
        if not appnode_info:
            return

        body = {"appnode": appnode_info}
        self._update("/appnodes/%s" % base.getid(appnode), body)
