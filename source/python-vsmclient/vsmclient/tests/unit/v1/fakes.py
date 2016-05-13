# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright (c) 2011 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

from vsmclient import client as base_client
from vsmclient.tests.unit import fakes
from vsmclient.tests.unit import utils
from vsmclient.v1 import client


def _stub_appnode(**kwargs):
    appnode = {
        'id': '1234',
        'os_username': 'admin',
        'os_password': 'admin',
        'os_tenant_name': 'admin',
        'os_auth_url': 'http://192.168.100.100:5000/v2.0',
        'os_region_name': 'RegionOne',
        'ssh_user': 'root',
        'uuid': '00000000-0000-0000-0000-000000000000',
        'ssh_status': 'reachable',
        'log_info': None
    }
    appnode.update(kwargs)
    return appnode


class FakeClient(fakes.FakeClient, client.Client):

    def __init__(self, *args, **kwargs):
        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = FakeHTTPClient(**kwargs)

    # def get_volume_api_version_from_endpoint(self):
    #     return self.client.get_volume_api_version_from_endpoint()


class FakeHTTPClient(base_client.HTTPClient):

    def __init__(self, **kwargs):
        self.username = 'username'
        self.password = 'password'
        self.auth_url = 'auth_url'
        self.callstack = []
        self.management_url = 'http://10.0.2.15:8776/v1/fake'

    def _cs_request(self, url, method, **kwargs):
        # Check that certain things are called correctly
        if method in ['GET', 'DELETE']:
            assert 'body' not in kwargs
        elif method == 'PUT':
            assert 'body' in kwargs

        # Call the method
        args = urlparse.parse_qsl(urlparse.urlparse(url)[4])
        kwargs.update(args)
        munged_url = url.rsplit('?', 1)[0]
        munged_url = munged_url.strip('/').replace('/', '_').replace('.', '_')
        munged_url = munged_url.replace('-', '_')

        callback = "%s_%s" % (method.lower(), munged_url)

        if not hasattr(self, callback):
            raise AssertionError('Called unknown API method: %s %s, '
                                 'expected fakes method name: %s' %
                                 (method, url, callback))

        # Note the call
        self.callstack.append((method, url, kwargs.get('body', None)))
        status, headers, body = getattr(self, callback)(**kwargs)
        r = utils.TestResponse({
            "status_code": status,
            "text": body,
            "headers": headers,
        })
        return r, body

        if hasattr(status, 'items'):
            return utils.TestResponse(status), body
        else:
            return utils.TestResponse({"status": status}), body

    # def get_volume_api_version_from_endpoint(self):
    #     magic_tuple = urlparse.urlsplit(self.management_url)
    #     scheme, netloc, path, query, frag = magic_tuple
    #     return path.lstrip('/').split('/')[0][1:]

    #
    # Appnodes
    #

    def get_appnodes(self, **kw):
        return (200, {}, {'appnodes': [
            _stub_appnode(),
        ]})

    def post_appnodes(self, body, **kw):
        return (201, {}, {})
