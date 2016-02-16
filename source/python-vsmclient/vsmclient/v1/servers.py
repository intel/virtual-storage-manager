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
Server interface.
"""

import urllib
from vsmclient import base


class Server(base.Resource):
    """"""
    def __repr__(self):
        return "<Server: %s>" % self.id

    def delete(self):
        """Delete this server."""
        self.manager.delete(self)

    def update(self, **kwargs):
        """"""
        self.manager.update(self, **kwargs)

class ServerManager(base.ManagerWithFind):
    """
    Manage :class:`Server` resources.
    """
    resource_class = Server

    def create(self, name):

        """
        Create a server.
        """

        body = {'server': {'name': name,
                           }}
        return self._create('/servers', body, 'server')

    def get(self, server_id):
        """
        Get a server.

        :param server_id: The ID of the server to delete.
        :rtype: :class:`Server`
        """
        return self._get("/servers/%s" % server_id, "server")

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all servers.

        :rtype: list of :class:`Server`
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

        ret = self._list("/servers%s%s" % (detail, query_string),
                          "servers")
        return ret

    def delete(self, server):
        """
        Delete a server.

        :param server: The :class:`Server` to delete.
        """
        self._delete("/servers/%s" % base.getid(server))

    def update(self, server, **kwargs):
        """

        :param vsm: The :class:`Server` to delete.
        """
        if not kwargs:
            return

        body = {"server": kwargs}

        self._update("/servers/%s" % base.getid(server), body)

    def _action(self, action, server, info=None, **kwargs):
        """
        Perform a server "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/servers/%s/action' % base.getid(server)
        return self.api.client.post(url, body=body)

    def add(self, servers=[]):
        """
        add servers
        """
        url = "/servers/add"
        return self.api.client.post(url, body={"servers":servers})

    def remove(self, servers=[]):
        """
        remove servers
        """
        url = "/servers/remove"
        return self.api.client.post(url, body={"servers":servers})

    def reset_status(self, servers=[]):
        """
        :param servers:
        :return:
        """
        url = "/servers/reset_status"
        return self.api.client.post(url, body={"servers": servers})

    def start(self, servers=None):
        """
        Start servers
        """
        url = "/servers/start"
        return self.api.client.post(url, body={"servers":servers})

    def stop(self, servers=None):
        """
        Stop servers
        """
        url = "/servers/stop"
        return self.api.client.post(url, body={"servers":servers})

    def ceph_upgrade(self, body=None):
        """
        ceph_upgrade
        """
        url = "/servers/ceph_upgrade"
        ret = self.api.client.post(url, body=body)
        print 'vsmclient ---ceph upgrade==',ret
        return ret
