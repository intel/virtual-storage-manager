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
import sys
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy

from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import views
from django import template
from vsm_dashboard.common.horizon.text import TextRenderer
from vsm_dashboard.api import vsm as vsmapi
from .tables import ListServerTable
from .tables import AddServerTable
from .tables import RemoveServerTable
from .tables import AddServerTable2
from .tables import AddMonitorTable
from .tables import RemoveMonitorTable
from .tables import StartServerTable
from .tables import StopServerTable
from django.http import HttpResponse
from .utils import get_server_list
from .utils import get_zone_list

import json
LOG = logging.getLogger(__name__)
from django.core.context_processors import csrf

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
        context['verbose_name'] = getattr(self, "verbose_name", "")
        context['submit_btn'] = getattr(self, "submit_btn", {})
        if self.request.is_ajax():
            context['hide'] = True
        return context

class IndexView(tables.DataTableView):
    table_class = ListServerTable
    template_name = 'vsm/storageservermgmt/index.html'

    def get_data(self):
        servers = get_server_list(self.request, )
        return servers

#Edit the class by XuShouan
class AddServersView(tables.DataTableView):
    table_class = AddServerTable
    verbose_name = "Add Servers"
    template_name = 'vsm/storageservermgmt/serversaction.html'

    def get_data(self):
        servers = get_server_list(self.request, lambda x: x['status'] == "available" or 
                                 ((x['type'].strip() == "monitor" or x['type'].strip() == "monitor,") \
                                  and x['status'] == "Active"))
        zone_list = get_zone_list(self.request)

        for server in servers:
            server.update({"zone_list": {"choices": zone_list, "value":server['zone_id']}})
            del server['is_monitor']
            del server['zone']

        return servers

#Edit the class by XuShouan
class RemoveServersView(tables.DataTableView):
    table_class = RemoveServerTable
    verbose_name = "Remove Servers"
    template_name = 'vsm/storageservermgmt/serversaction.html'

    def get_data(self):
        return get_server_list(self.request, lambda x: x['status'] in ("Active", "999999999"))


#Edit the class by XuShouan
class AddMonitorsView(tables.DataTableView):
    table_class = AddMonitorTable
    template_name = 'vsm/storageservermgmt/serversaction.html'
    verbose_name = "Add Monitors"
    def get_data(self):
        servers = get_server_list(self.request, (
            lambda x: x['status'] in ("Active", "available"),
            lambda x: not (x['status'] == "Active" and "monitor" in x['type']),))
        for server in servers:
            del server['is_monitor']
        return servers

#Edit the class by XuShouan
class RemoveMonitorsView(tables.DataTableView):
    table_class = RemoveMonitorTable
    template_name = 'vsm/storageservermgmt/serversaction.html'
    verbose_name = "Remove Monitors"

    def get_data(self):
        servers = get_server_list(self.request, (
            lambda x: x['status'] == "Active",
            lambda x: "monitor" in x['type'],))
        return servers


#Edit the class by XuShouan
class StartServersView(tables.DataTableView):
    table_class = StartServerTable
    template_name = 'vsm/storageservermgmt/serversaction.html'
    verbose_name = "Start Servers"
    def get_data(self):
        return get_server_list(self.request, lambda x:x['status'] == "Stopped")

#Edit the class by XuShouan
class StopServersView(tables.DataTableView):
    table_class = StopServerTable
    template_name = 'vsm/storageservermgmt/serversaction.html'
    verbose_name = "Stop Servers"
    def get_data(self):
        return get_server_list(self.request, lambda x:x['status'] == "Active")




class ServersActionViewBase(ModalEditTableMixin, tables.DataTableView):
    #success_url = reverse_lazy('horizon:vsm:storageservermgmt:index')

    def get_data(self):
        raise NotImplementedError


class AddServersView2(AddServersView):
    table_class = AddServerTable2

class OsdsText(TextRenderer):
    name = "osds"

    def get_text(self):
        osds = vsmapi.osd_status(self.request)
        osd_list = []
        for _osd in osds:
            osd = {
                "osd_name": _osd.osd_name,
                "server": _osd.service['host'],
                "storage_group": _osd.storage_group['name'],
                "capacity_total": _osd.device['total_capacity_kb'],#TODO dict to obj ?
                "capacity_used": _osd.device['used_capacity_kb'],
                "capacity_avail": _osd.device['avail_capacity_kb'],
                }
            osd_list.append(osd)
        return json.dumps(osd_list) 

class StorageGroupsText(TextRenderer):
    name = "storage_groups"
    def get_text(self):
        storage_groups = vsmapi.storage_group_status(self.request)
        storage_group_list = []
        for _storage_group in storage_groups:
            storage_group = {
                "storage_group_name": _storage_group.name,
                "capacity_total": _storage_group.capacity_total,
                "capacity_used": _storage_group.capacity_used,
                "capacity_avail": _storage_group.capacity_avail,
                }
            storage_group_list.append(storage_group)
        return json.dumps(storage_group_list) 

class StorageGroupThresholdText(TextRenderer):
    name = "storage_group_threshold"
    def get_text(self):
        _cfg = vsmapi.get_setting_dict(self.request)
        threshold = {}
        threshold['full_threshold'] = _cfg["storage_group_full_threshold"]
        threshold['near_full_threshold'] = _cfg["storage_group_near_full_threshold"]
        return json.dumps(threshold)

class TextMixin(object):
    def get_context_data(self, **kwargs):
        context = super(TextMixin, self).get_context_data(**kwargs)
        context['osds_text'] = OsdsText(self.request) 
        context['storage_groups_text'] = StorageGroupsText(self.request)
        context['storage_group_threshold_text'] = StorageGroupThresholdText(self.request)
        return context


def ServersAction(request, action):
    data = json.loads(request.body)
    # TODO add cluster_id in data
    if not len(data):
        status = "error"
        msg = "No server selected"
    else:
        # TODO add cluster_id in data
        for i in range(0, len(data)):
            data[i]['cluster_id'] = 1
        # TODO add cluster_id in data

        if action == "add":
            vsmapi.add_servers(request, data)
            status = "info"
            msg = "Began to Add Servers"
        elif action == "remove":
            vsmapi.remove_servers(request, data)
            status = "info"
            msg = "Began to Remove Servers"
        elif action == "start":
            vsmapi.start_server(request, data)
            status = "info"
            msg = "Began to Start Servers"
        elif action == "stop":
            LOG.debug("DEBUG in server action %s" % data)
            vsmapi.stop_server(request, data)
            status = "info"
            msg = "Began to Stop Servers"

    resp = dict(message=msg, status=status, data="")
    resp = json.dumps(resp)
    return HttpResponse(resp)

def ResetStatus(request, server_id):
    resp = dict(message="Began to Reset Status", status="info")
    resp = json.dumps(resp)
    vsmapi.reset_status(request, server_id)
    return HttpResponse(resp)

