# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel
# All Rights Reserved.
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
Use socket to transfer msg.
"""

import json
import urllib2
from vsm import flags
from vsm.openstack.common import log as logging
from vsm import utils
import token

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class WSGIClient(object):
    """WSGI Client service to get data from vsm-api.

    When used by vsm-agen, the password is get from server.manifest.
    """
    def __init__(self, vsm_api_ip='vsm_api_ip', info='token-tenantid'):
        """Initialized the url requestion and RUL."""
        self._vsm_api_ip = vsm_api_ip
        self._token = "-".join(info.split("-")[0:-1])
        self._tenant_id = info.split("-")[-1]
        self._vsm_url = "http://%s:%s/v1/%s" % \
                        (self._vsm_api_ip,
                         8778,
                         self._tenant_id)
        LOG.info('Agent token = %s, access url = %s' % \
                 (self._token, self._vsm_url))

    def index(self):
        """Use this method to get cluster's critial information."""

        req_url = self._vsm_url + "/agents"
        req = urllib2.Request(req_url)
        req.get_method = lambda: 'GET'
        req.add_header("content-type", "application/json")
        req.add_header("X-Auth-Token", self._token)
        resp = urllib2.urlopen(req)
        recive_data = json.loads(resp.read())
        return recive_data

    def send(self, data, method, url="agents"):
        """Use parameter to contruct wsgi request to server.

        Below is an example how to send wsgi request to vsm-api server.

            url = "http://%(host)s:%(port)s/gw/%(id)/agents"
            req = urllib2.Request(url,
                  data=json.dumps({"agent":{"name":"test"}}))
            req.get_method = lambda: "POST"
            req.add_header("content-type", "application/json")
            resp = urllib2.urlopen(req)
            configs = json.loads(resp.read())

        It's easy to transfer %(id), for simple, you can juse transfer 1.
        """
        pass
