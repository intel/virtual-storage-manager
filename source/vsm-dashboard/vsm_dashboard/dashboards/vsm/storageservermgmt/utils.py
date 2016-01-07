
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
import logging
LOG = logging.getLogger(__name__)

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

def checkbox_transform(text):
    return """<input type="checkbox" name="checkbox1" value="checkbox"> text """

def get_server_list(request, filters=[]):
        _zones = []
        _servers = []
        #_servers= vsmapi.get_server_list(self.request,)
        try:
            _servers = api.vsm.get_server_list(request,)
            _zones = api.vsm.get_zone_list(request,)
            logging.debug("resp body in view: %s" % _servers)
        except:
            exceptions.handle(request,
                              _('Unable to retrieve sever list. '))

        zones = {}
        for _zone in _zones:
            zones.setdefault(_zone.id, _zone.name)

        servers = []
        for _server in _servers:
            server = {"id": _server.id,
                        "name": _server.host,
                        "primary_public_ip": _server.primary_public_ip,
                        "secondary_public_ip": _server.secondary_public_ip,
                        "cluster_ip": _server.cluster_ip,
                        "zone_id": _server.zone_id,
                        "ceph_ver": _server.ceph_ver,
                        "zone": "",
                        "osds": _server.osds,
                        "type": _server.type,
                        "status": _server.status}

            if "monitor" in _server.type:
                server['is_monitor'] = "yes"
            else:
                server['is_monitor'] = "no"

            if "storage" in _server.type:
                server['is_storage'] = "yes"
            else:
                server['is_storage'] = "no"

            if _server.zone_id in zones:
                server['zone'] = zones[_server.zone_id]

            servers.append(server)

        LOG.info("get server_list filter type: %s" % type(filters))
        if hasattr(filters, "__call__"):
            filters = [filters]
        LOG.info("get server_list filters: %s" % str(filters))
        if hasattr(filters, "__iter__"):
            for f in filters:
                servers = filter(f, servers)

        return servers

def get_zone_list(request):
        _zones = []
        try:
            _zones = api.vsm.get_zone_list(request,)
        except:
            exceptions.handle(request,
                              _('Unable to retrieve sever list. '))
        for _zone in _zones:
            zones.setdefault(_zone['id'], _zone['name'])
        zone_list = zones.items()
        return zone_list

def get_zone_not_in_crush_list(request):
        _zones = []
        try:
            _zones = api.vsm.get_zone_not_in_crush_list(request,)
        except:
            exceptions.handle(request,
                              _('Unable to retrieve sever list. '))
        _zones = _zones['zone_not_in_crush']
        return get_zone_list_format(_zones)

def get_zone_as_osd_location(request):
        _zones = []
        try:
            _zones = api.vsm.osd_locations_choices_by_type(request,)
        except:
            exceptions.handle(request,
                              _('Unable to retrieve sever list. '))
        _zones = _zones['osd_locations_choices']
        return get_zone_list_format(_zones)

def get_zone_list_format(zones):
        zones_dict = {}
        for _zone in zones:
            print 'dir-----1111---',dir(_zone)
            print 'type----1111---',type(_zone)
            zones_dict.setdefault(_zone['id'], _zone['name'])
        zone_list = zones_dict.items()
        return zone_list