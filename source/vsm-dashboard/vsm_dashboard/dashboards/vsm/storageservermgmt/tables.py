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
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict
from django import forms

from django.utils.safestring import mark_safe
#from vsm_dashboard.dashboards.admin.instances.tables import \
#        AdminUpdateRow

from horizon import tables
from horizon.utils import html
from horizon import exceptions
from vsm_dashboard.api import vsm as vsmapi

from .utils import checkbox_transform

STRING_SEPARATOR = "__"
LOG = logging.getLogger(__name__)

class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, id):
        # todo update zone info in apiclient CEPH_LOG
        try:
            _zones = vsmapi.get_zone_list(request,)
        except:
            exceptions.handle(request,
                              _('Unable to retrieve sever list. '))
        zones = {}
        for _zone in _zones:
            zones.setdefault(_zone.id, _zone.name)

        _server = vsmapi.get_server(request, id)
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

        return server

STATUS_DISPLAY_CHOICES = (
    ("resize", "Resize/Migrate"),
    ("verify_resize", "Confirm or Revert Resize/Migrate"),
    ("revert_resize", "Revert Resize/Migrate"),
)

class ResetStatus(tables.BatchAction):
    name = "reset"
    action_present = _("Reset")
    action_past = _("Status Rested")
    data_type_singular = _("Server Status")
    data_type_plural = _("Servers Status")
    classes = ("reset-status-action", "")

    def allowed(self, request, instance=None):
        return (instance["status"] in ("running", "stopping", "removing", "adding", "starting")) or ("ERROR" in instance["status"])

    def action(self, request, obj_id):
        LOG.info("RESET_STATUS")
        vsmapi.servers.reset_status(request, [obj_id])

class AddServersAction(tables.LinkAction):
    name = "add_servers"
    verbose_name = _("Add Servers")
    url = "horizon:vsm:storageservermgmt:addserversview"
    classes = ("ajax-modal", "btn-create")

class RemoveServersAction(tables.LinkAction):
    name = "remove_servers"
    verbose_name = _("Remove Servers")
    url = "horizon:vsm:storageservermgmt:removeserversview"
    classes = ("ajax-modal", "btn-create")

class AddMonitorsAction(tables.LinkAction):
    name = "add_monitors"
    verbose_name = _("Add Monitors")
    url = "horizon:vsm:storageservermgmt:addmonitorsview"
    classes = ("ajax-modal", "btn-create")

class RemoveMonitorsAction(tables.LinkAction):
    name = "remove_monitors"
    verbose_name = _("Remove Monitors")
    url = "horizon:vsm:storageservermgmt:removemonitorsview"
    classes = ("ajax-modal", "btn-create")

class StartServersAction(tables.LinkAction):
    name = "start_servers"
    verbose_name = _("Start Servers")
    url = "horizon:vsm:storageservermgmt:startserversview"
    classes = ("ajax-modal", "btn-create")

class StopServersAction(tables.LinkAction):
    name = "stop_servers"
    verbose_name = _("Stop Servers")
    url = "horizon:vsm:storageservermgmt:stopserversview"
    classes = ("ajax-modal", "btn-create")

class ListServerTableBase(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("available", True),
        ("Active", True),
        ("Stopped", True),
    )

    server_id = tables.Column("id", verbose_name=_("ID"), classes=("server_id",))
    name = tables.Column("name", verbose_name=_("Name"))
    primary_public_ip = tables.Column("primary_public_ip", verbose_name=_("Management Address"))
    secondary_public_ip = tables.Column("secondary_public_ip", verbose_name=_("Ceph Public Address"))
    cluster_ip = tables.Column("cluster_ip", verbose_name=_("Ceph Cluster Address"))
    osds = tables.Column("osds", verbose_name=_("OSDs (Data Drives)"))
    is_monitor = tables.Column("is_monitor", classes=("monitor_tag",), verbose_name=_("Monitor"))
    zone = tables.Column("zone", classes=("zone",), verbose_name=_("Zone"))
    status = tables.Column("status", status=True,
                            status_choices=STATUS_CHOICES,
                            display_choices=STATUS_DISPLAY_CHOICES,
                            verbose_name=_("Status"))

#    createdBy = tables.Column("createdBy", verbose_name=_("Created By"))
#    cluster = tables.Column("clusterName", verbose_name=_("Cluster"))

    class Meta:
        name = "server_list_base"
        verbose_name = _("Cluster Server List")
        table_actions = (AddServersAction, RemoveServersAction, 
                AddMonitorsAction, RemoveMonitorsAction)
        status_columns = ['status']
        row_class = UpdateRow

    def get_object_id(self, datum):
        if hasattr(datum, "id"):
            return datum.id
        else:
            return datum["id"]

    def get_object_display(self, datum):
        if hasattr(datum, "name"):
            return datum.id
        else:
            return datum["name"]

class ListServerTable(ListServerTableBase):
    STATUS_CHOICES = (
        ("active", True),
        ("available", True),
        ("Active", True),
        ("Stopped", True),
    )

    server_id = tables.Column("id", verbose_name=_("ID"), classes=("server_id",))
    name = tables.Column("name", verbose_name=_("Name"))
    primary_public_ip = tables.Column("primary_public_ip", verbose_name=_("Management Address"), attrs={"data-type": "ip"})
    secondary_public_ip = tables.Column("secondary_public_ip", verbose_name=_("Ceph Public Address"), attrs={"data-type": "ip"})
    cluster_ip = tables.Column("cluster_ip", verbose_name=_("Ceph Cluster Address"), attrs={"data-type": "ip"})
    osds = tables.Column("osds", verbose_name=_("OSDs (Data Drives)"))
    is_monitor = tables.Column("is_monitor", classes=("monitor_tag",), verbose_name=_("Monitor"))
    zone = tables.Column("zone", classes=("zone",), verbose_name=_("Zone"))
    status = tables.Column("status", status=True,
                            status_choices=STATUS_CHOICES,
                            display_choices=STATUS_DISPLAY_CHOICES,
                            verbose_name=_("Status"))
    class Meta:
        name = "server_list"
        verbose_name = _("Cluster Server List")
        table_actions = (AddServersAction, RemoveServersAction,
                AddMonitorsAction, RemoveMonitorsAction, StartServersAction, StopServersAction)
        status_columns = ['status']
        row_class = UpdateRow
        multi_select = False
        row_actions = (ResetStatus,)

def empty_value_maker(type, name, value, attrs=None):
    def _empty_value_caller(datum):
        if type == "text":
            widget = forms.TextInput()
        elif type == "choice":
            widget = forms.ChoiceField().widget
        elif type == "checkbox":
            widget = forms.CheckboxInput()
        data = dict(name=name, value=value)
        if name in datum.keys():
            data.update(datum[name])
        if attrs:
            data.update(dict(attrs=attrs))
        data = widget.render(**data)
        return data
    return _empty_value_caller

class AddServerTable(tables.DataTable):

    server_id = tables.Column("id", verbose_name=_("ID"), classes=("server_id",))
    name = tables.Column("name", verbose_name=_("Name"))
    primary_public_ip = tables.Column("primary_public_ip", verbose_name=_("Management Address"))
    secondary_public_ip = tables.Column("secondary_public_ip",
        verbose_name=_("Ceph Public Address"))
    cluster_ip = tables.Column("cluster_ip", verbose_name=_("Ceph Cluster Address"))
    zone = tables.Column("zone", verbose_name=_("Zone"), 
        classes=('zone',), empty_value=empty_value_maker("choice","zone_list","",{"style":"width:80px"}))
    osds = tables.Column("osds", verbose_name=_("OSDs (Data Drives)"))
    is_monitor = tables.Column("is_monitor", verbose_name=_("Monitor"),
        classes=('monitor',), empty_value=empty_value_maker("checkbox","is_monitor","")) 
    is_storage = tables.Column("is_storage", verbose_name=_("Storage"), classes=('storage',),
        empty_value=empty_value_maker("checkbox","is_storage",1), hidden=True) 
    server_status = tables.Column("status", verbose_name=_("Server Status"), classes=('server_status',))
    #createdBy = tables.Column("createdBy", verbose_name=_("Created By"))
    #cluster = tables.Column("clusterName", verbose_name=_("Cluster"))

    class Meta:
        multi_select = True
        name = "tServers"
        verbose_name = _("Add Servers")
        

    def get_object_id(self, datum):
        if hasattr(datum, "id"):
            return datum.id
        else:
            return datum["id"]

    def get_object_display(self, datum):
        if hasattr(datum, "name"):
            return datum.id
        else:
            return datum["name"]

class RemoveServerTable(tables.DataTable):

    server_id = tables.Column("id", verbose_name=_("ID"), classes=("server_id",))
    name = tables.Column("name", classes=("server_name",), verbose_name=_("Name"))
    primary_public_ip = tables.Column("primary_public_ip", verbose_name=_("Management Address"))
    secondary_public_ip = tables.Column("secondary_public_ip",
        verbose_name=_("Ceph Public Address"))
    cluster_ip = tables.Column("cluster_ip", verbose_name=_("Ceph Cluster Address"))
    zone = tables.Column("zone", verbose_name=_("Zone"),
        classes=('zone',), empty_value=empty_value_maker("choice","zone_list","",{"style":"width:80px"}))
    osds = tables.Column("osds", verbose_name=_("OSDs (Data Drives)"))
    is_monitor = tables.Column("is_monitor", classes=("monitor_tag",), verbose_name=_("Monitor"))
    remove_monitor = tables.Column("remove_monitor", verbose_name=_("Monitor"),
        classes=('remove_monitor',), empty_value=empty_value_maker("checkbox","remove_monitor", True),
        hidden=True)
    remove_storage = tables.Column("remove_storage", verbose_name=_("Storage"), classes=('remove_storage',),
        empty_value=empty_value_maker("checkbox","remove_storage",True), hidden=True)
    server_status = tables.Column("status", verbose_name=_("Server Status"), classes=('server_status',))
    #createdBy = tables.Column("createdBy", verbose_name=_("Created By"))
    #cluster = tables.Column("clusterName", verbose_name=_("Cluster"))

    class Meta:
        multi_select = True
        name = "tServers"
        verbose_name = _("Remove Servers")

    def get_object_id(self, datum):
        if hasattr(datum, "id"):
            return datum.id
        else:
            return datum["id"]

    def get_object_display(self, datum):
        if hasattr(datum, "name"):
            return datum.id
        else:
            return datum["name"]

class AddServerTable2(AddServerTable):
    is_storage = tables.Column("is_storage", verbose_name=_("Storage"), classes=('storage',),
        empty_value=empty_value_maker("checkbox","is_storage",""))

    class Meta:
        name = "serversaction"
        verbose_name = _("Servers")
        multi_select = True

class AddMonitorTable(ListServerTableBase):
    monitor = tables.Column("is_monitor", verbose_name=_("isMonitor"), hidden=True,
        classes=('monitor',), empty_value=empty_value_maker("checkbox","", 1))
    class Meta:
        name = "tServers"
        verbose_name = _("Add Monitors")
        multi_select = True

class RemoveMonitorTable(ListServerTableBase):
    remove_monitor = tables.Column("remove_monitor", verbose_name=_("Monitor"),
        classes=('remove_monitor',), empty_value=empty_value_maker("checkbox","remove_monitor", True),
        hidden=True)
    remove_storage = tables.Column("remove_storage", verbose_name=_("Storage"), classes=('remove_storage',),
        empty_value=empty_value_maker("checkbox","remove_storage",False), hidden=True)

    class Meta:
        name = "tServers"
        verbose_name = _("Remove Monitors")
        multi_select = True

class StartServerTable(ListServerTableBase):

    class Meta:
        name = "tServers"
        verbose_name = _("Start Servers")
        multi_select = True

class StopServerTable(ListServerTableBase):

    class Meta:
        name = "tServers"
        verbose_name = _("Stop Servers")
        multi_select = True
