
# Copyright 2014 Intel Corporation, All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the"License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

import time
import json
import urllib2

from django.utils.dateparse import parse_datetime
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from vsm_dashboard import api

from horizon import exceptions

from .test_data import json as test_json

def correlate_tenants(request, instances):
    # Gather our tenants to correlate against IDs
    try:
        tenants = api.keystone.tenant_list(request, admin=True)
    except:
        tenants = []
        msg = _('Unable to retrieve instance tenant information.')
        exceptions.handle(request, msg)
    tenant_dict = SortedDict([(t.id, t) for t in tenants])
    for inst in instances:
        tenant = tenant_dict.get(inst.tenant_id, None)
        inst._apiresource._info['tenant'] = tenant._info
        inst.tenant = tenant

def correlate_flavors(request, instances):
    # Gather our flavors to correlate against IDs
    try:
        flavors = api.nova.flavor_list(request)
    except:
        flavors = []
        msg = _('Unable to retrieve instance size information.')
        exceptions.handle(request, msg)

    flavors_dict = SortedDict([(f.id, f) for f in flavors])
    for inst in instances:
        flavor = flavors_dict.get(inst.flavor["id"], None)
        inst._apiresource._info['flavor'] = flavor._info
        inst.flavor = flavor

def correlate_users(request, instances):
    # Gather our users to correlate against IDs
    try:
        users = api.keystone.user_list(request)
    except:
        users = []
        msg = _('Unable to retrieve instance user information.')
        exceptions.handle(request, msg)
    user_dict = SortedDict([(u.id, u) for u in users])
    for inst in instances:
        user = user_dict.get(inst.user_id, None)
        inst._apiresource._info['user'] = user._info
        inst.user = user

def calculate_ages(instances):
    for instance in instances:
        dt = parse_datetime(instance._apiresource.created)
        timestamp = time.mktime(dt.timetuple())
        instance._apiresource._info['created'] = timestamp
        instance.age = dt

def get_fake_instances_data(request):
    import json
    from novaclient.v1_1.servers import Server, ServerManager
    from horizon.api.nova import Server as HServer
    instances = [HServer(Server(ServerManager(None), i), request)
                 for i in json.loads(test_json)]
    for i in instances:
        i._loaded = True
    instances += instances
    return instances

def get_instances_data(request):
    instances = api.nova.server_list(request, all_tenants=True)

    # Get the useful data... thanks Nova :-P
    if instances:
        correlate_flavors(request, instances)
        correlate_tenants(request, instances)
        correlate_users(request, instances)
        calculate_ages(instances)

    return instances


class GenAuthToken(object):
    """Generate token from vsm-api WSGI service."""

    def __init__(self, tenant_name, username, password, host, region_name):
        """Initialized the url requestion and RUL."""
        self._tenant_namt = tenant_name
        self._username = username
        self._password = password
        self._auth_url = "http://%s:5000/v2.0/tokens" % host
        self._region_name = region_name
        self._token = None
        self._url = None

    def get_token(self):
        """Get auth info from keystone."""
        auth_data = {
            "auth": {
                "tenantName": self._tenant_namt,
                "passwordCredentials":{
                    "username": self._username,
                    "password": self._password
                }
            }
        }

        auth_request = urllib2.Request(self._auth_url)
        auth_request.add_header("content-type", "application/json")
        auth_request.add_header('Accept', 'application/json')
        auth_request.add_header('User-Agent', 'python-mikeyp')
        auth_request.add_data(json.dumps(auth_data))
        auth_response = urllib2.urlopen(auth_request)
        response_data = json.loads(auth_response.read())

        self._token = response_data['access']['token']['id']

        service_list = response_data['access']['serviceCatalog']
        for service in service_list:
            if service['type'] == 'volume' and service['name'] == 'cinder':
                for endpoint in service['endpoints']:
                    if self._region_name != None and endpoint['region'] == self._region_name:
                        self._url = endpoint['publicURL']
                        break
                    elif self._region_name == None or self._region_name == "" and len(service['endpoints']) == 1:
                        self._url = endpoint['publicURL']
                        break

        url_id = self._url.split('/')[-1]
        host = self._url.split('/')[2].split(':')[0]
        return self._token, url_id, host

def list_cinder_service(host, token, tenant_id):
    req_url = "http://%s:8776/v1/%s" % (host, tenant_id) + "/os-services"
    req = urllib2.Request(req_url)
    req.get_method = lambda: 'GET'
    req.add_header("content-type", "application/json")
    req.add_header("X-Auth-Token", token)
    resp = urllib2.urlopen(req)
    cinder_service_dict = json.loads(resp.read())
    cinder_service_list = cinder_service_dict['services']
    return cinder_service_list