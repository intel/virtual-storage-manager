
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

def from_keystone_v3(tenant_name, username, password, auth_url, region_name):
    auth_url = auth_url + "/auth/tokens"
    user_id = username
    user_password = password
    project_id = tenant_name
    auth_data = {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "id": user_id,
                        "password": user_password
                    }
                }
            },
            "scope": {
                "project": {
                    "id": project_id
                }
            }
        }
    }
    auth_request = urllib2.Request(auth_url)
    auth_request.add_header("content-type", "application/json")
    auth_request.add_header('Accept', 'application/json')
    auth_request.add_header('User-Agent', 'python-mikeyp')
    auth_request.add_data(json.dumps(auth_data))
    auth_response = urllib2.urlopen(auth_request)
    response_data = json.loads(auth_response.read())
    services_list = response_data['token']['catalog']
    endpoints_list = []
    _url = None
    for service in services_list:
        service_type = service['type']
        service_name = service['name']
        if service_type == "volume" and service_name == "cinder":
            endpoints_list = service['endpoints']
            break
    for endpoint in endpoints_list:
        interface = endpoint['interface']
        region_id = endpoint['region_id']
        if region_name:
            if interface == "public" and region_id == region_name:
                _url = endpoint['url']
                break
        else:
            if len(endpoints_list) == 3:
                _url = endpoint['url']
                break
    host = _url.split('/')[2].split(':')[0]
    _token = auth_response.info().getheader('X-Subject-Token')
    return _token, host



def from_keystone_v2(tenant_name, username, password, auth_url, region_name):
    auth_url = auth_url + "/tokens"
    auth_data = {
        "auth": {
            "tenantName": tenant_name,
            "passwordCredentials":{
                "username": username,
                "password": password
            }
        }
    }

    auth_request = urllib2.Request(auth_url)
    auth_request.add_header("content-type", "application/json")
    auth_request.add_header('Accept', 'application/json')
    auth_request.add_header('User-Agent', 'python-mikeyp')
    auth_request.add_data(json.dumps(auth_data))
    auth_response = urllib2.urlopen(auth_request)
    response_data = json.loads(auth_response.read())

    _token = response_data['access']['token']['id']

    service_list = response_data['access']['serviceCatalog']
    _url = None
    for service in service_list:
        if service['type'] == 'volume' and service['name'] == 'cinder':
            for endpoint in service['endpoints']:
                if region_name != None and endpoint['region'] == region_name:
                    _url = endpoint['publicURL']
                    break
                elif region_name == None or region_name == "" and len(service['endpoints']) == 1:
                    _url = endpoint['publicURL']
                    break

    url_id = _url.split('/')[-1]
    host = _url.split('/')[2].split(':')[0]
    return _token, url_id, host