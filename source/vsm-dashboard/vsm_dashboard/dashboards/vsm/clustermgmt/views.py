# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Corporation, All Rights Reserved.
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

import logging
import os
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import tables
from .tables import ListServerTable
from .tables import CreateClusterTable
from django.http import HttpResponse
from vsm_dashboard.api import vsm as vsmapi

import json
LOG = logging.getLogger(__name__)

class ModalEditTableMixin(object):
    def get_template_names(self):
        if self.request.is_ajax():
            if not hasattr(self, "ajax_template_name"):
                # Transform standard template name to ajax name (leading "_")
                bits = list(os.path.split(self.template_name))
                bits[1] = "".join(("_", bits[1]))
                self.ajax_template_name = os.path.join(*bits)
            template = self.ajax_template_name
        else:
            template = self.template_name
        return template

    def get_context_data(self, **kwargs):
        context = super(ModalEditTableMixin, self).get_context_data(**kwargs)
        if self.request.is_ajax():
            context['hide'] = True
        return context

class IndexView(tables.DataTableView):
    table_class = ListServerTable
    template_name = 'vsm/clustermgmt/index.html'

    def get_data(self):
        _servers = []
        #_servers= vsmapi.get_server_list(self.request,)
        try:
            _servers = vsmapi.get_server_list(self.request,)
            _zones = vsmapi.get_zone_list(self.request)
            if _servers:
                logging.debug("resp body in view: %s" % _servers)
        except:
            exceptions.handle(self.request,
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
                        "zone": "",
                        "osds": _server.osds,
                        "type": _server.type,
                        "status": _server.status}

            if "monitor" in _server.type:
                server['is_monitor'] = "yes"
            else:
                server['is_monitor'] = "no"
            if _server.zone_id in zones:
                server['zone'] = zones[_server.zone_id]
                server['ismonitor'] = ''
                server['isstorage'] = ''
            servers.append(server)
        return servers

class CreateClusterView(ModalEditTableMixin, tables.DataTableView):
    table_class = CreateClusterTable
    template_name = 'vsm/flocking/createcluster.html'
    #success_url = reverse_lazy('horizon:vsm:storageservermgmt:index')

    def get_data(self):
        _zones = []
        _servers = []
        #_servers= vsmapi.get_server_list(self.request,)
        try:
            _servers = vsmapi.get_server_list(self.request,)
            _zones = vsmapi.get_zone_list(self.request,)
            logging.debug("resp body in view: %s" % _servers)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve sever list. '))

        zones = {}
        for _zone in _zones:
            zones.setdefault(_zone.id, _zone.name)
        zone_list = zones.items()

        servers = []
        for _server in _servers:
            if _server.status != 'available':
                continue

            server = {"id": _server.id,
                        "name": _server.host,
                        "primary_public_ip": _server.primary_public_ip,
                        "secondary_public_ip": _server.secondary_public_ip,
                        "cluster_ip": _server.cluster_ip,
                        "zone_id": _server.zone_id,
                        "osds": _server.osds,
                        "type": _server.type,
                        "status": _server.status}
            if "monitor" in _server.type:
                server['is_monitor'] = {"value": True}
                server['monitor'] = "yes"
            else:
                server['is_monitor'] = {"value": False}
                server['monitor'] = "no"
            if "storage" in _server.type:
                server['is_storage'] = {"value": True}
                server['storage'] = "yes"
            else:
                server['is_storage'] = {"value": False}
                server['storage'] = "no"
            if "mds" in _server.type:
                server['is_mds'] = {"value": True}
                server['mds'] = "yes"
            else:
                server['is_mds'] = {"value": False}
                server['mds'] = "no"
            if "rgw" in _server.type:
                server['is_rgw'] = {"value": True}
                server['rgw'] = "yes"
            else:
                server['is_rgw'] = {"value": False}
                server['rgw'] = "no"
            if _server.zone_id in zones:
                server['zone'] = zones[_server.zone_id]
            server['ismonitor'] = ''
            server['isstorage'] = ''
            servers.append(server)

        return servers

class IntegrateClusterView(ModalEditTableMixin, tables.DataTableView):
    table_class = CreateClusterTable
    template_name = 'vsm/flocking/createcluster.html'
    #success_url = reverse_lazy('horizon:vsm:storageservermgmt:index')

    def get_data(self):
        _zones = []
        _servers = []
        #_servers= vsmapi.get_server_list(self.request,)
        try:
            _servers = vsmapi.get_server_list(self.request,)
            _zones = vsmapi.get_zone_list(self.request,)
            logging.debug("resp body in view: %s" % _servers)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve sever list. '))

        zones = {}
        for _zone in _zones:
            zones.setdefault(_zone.id, _zone.name)
        zone_list = zones.items()

        servers = []
        for _server in _servers:
            if _server.status != 'available':
                continue

            server = {"id": _server.id,
                        "name": _server.host,
                        "primary_public_ip": _server.primary_public_ip,
                        "secondary_public_ip": _server.secondary_public_ip,
                        "cluster_ip": _server.cluster_ip,
                        "zone_id": _server.zone_id,
                        "osds": _server.osds,
                        "type": _server.type,
                        "status": _server.status}
            if "monitor" in _server.type:
                server['is_monitor'] = {"value": True}
                server['monitor'] = "yes"
            else:
                server['is_monitor'] = {"value": False}
                server['monitor'] = "no"
            if "storage" in _server.type:
                server['is_storage'] = {"value": True}
                server['storage'] = "yes"
            else:
                server['is_storage'] = {"value": False}
                server['storage'] = "no"
            if _server.zone_id in zones:
                server['zone'] = zones[_server.zone_id]
            servers.append(server)

        return servers

def ClusterAction(request, action):
    data = json.loads(request.body)
    
    if not len(data):
        status = "error"
        msg = "No server selected"
    else:
        if action == "create":
            vsmapi.create_cluster(request, data)
            status = "info"
            msg = "Began to Create Cluster"
        elif action == "integrate":
            vsmapi.integrate_cluster(request, data)
            status = "info"
            msg = "Began to integrate Cluster"
        else:
            status = "info"
            msg = "Began to Create Cluster"

    resp = dict(message=msg, status=status, data="")
    resp = json.dumps(resp)
    return HttpResponse(resp)

def CheckClusterExist(request):
    is_exsit = True
    pool_status = vsmapi.pool_status(request)
    server_list = vsmapi.get_server_list(None)
    status = [server.status for server in server_list]
    if len(pool_status) == 0 and 'Active' not in status:
        is_exsit = False
    resp = json.dumps({"is_exsit":is_exsit})
    return HttpResponse(resp)


def update_table(request):
    try:
        _zones = vsmapi.get_zone_list(request,)
    except Exception, e:
        exceptions.handle(request,_('Unable to retrieve sever list. '))

    #generate the zone list
    zones = {}
    for _zone in _zones:
        zones.setdefault(_zone.id, _zone.name)

    _server_list = vsmapi.get_server_list(request)
    _new_server_list = []
    for _server in _server_list:
        _zone_name = ""
        _is_monitor = "no"
        if _server.zone_id in zones:
            _zone_name = zones[_server.zone_id]
        if "monitor" in _server.type:
            _is_monitor = "yes"
        _new_server = {
            "id": _server.id,
            "name": _server.host,
            "primary_public_ip": _server.primary_public_ip,
            "secondary_public_ip": _server.secondary_public_ip,
            "cluster_ip": _server.cluster_ip,
            "zone_id": _server.zone_id,
            "zone": _zone_name,
            "osds": _server.osds,
            "type": _server.type,
            "status": _server.status,
            "is_monitor": _is_monitor
        }
        _new_server_list.append(_new_server)

    return HttpResponse(json.dumps(_new_server_list))