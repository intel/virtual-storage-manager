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


from django.utils.translation import ugettext_lazy as _
from django import forms

from horizon import tables
from horizon import exceptions
from vsm_dashboard.api import vsm as vsmapi

STRING_SEPARATOR = "__"

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

class CreateClusterAction(tables.LinkAction):
    name = "create_cluster"
    verbose_name = _("Create Cluster")
    url = "horizon:vsm:clustermgmt:createclusterview"
    classes = ("ajax-modal", "btn-primary")

    def allowed(self, request, datum):
        return all([x['status']=="available" for x in self.table.data])

class IntegrateClusterAction(tables.LinkAction):
    name = "integrate cluster"
    verbose_name = _("Integrate Cluster")
    url = "horizon:vsm:clustermgmt:integrateclusterview"
    classes = ("ajax-modal", "btn-primary")

    def allowed(self, request, datum):
        return True

class ListServerTable(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("available", True),
        ("Active", True),
    )

    server_id = tables.Column("id", verbose_name=_("ID"))
    name = tables.Column("name", verbose_name=_("Name"))
    primary_public_ip = tables.Column("primary_public_ip", verbose_name=_("Management Address"), attrs={"data-type": "ip"})
    secondary_public_ip = tables.Column("secondary_public_ip", verbose_name=_("Public Address"), attrs={"data-type": "ip"})
    cluster_ip = tables.Column("cluster_ip", verbose_name=_("Cluster Address"), attrs={"data-type": "ip"})
    osds = tables.Column("osds", verbose_name=_("OSDs"))
    is_monitor = tables.Column("is_monitor", verbose_name=_("Monitor"))
    zone = tables.Column("zone", classes=("zone",), verbose_name=_("Zone"))
    status = tables.Column("status", status=True,
                            status_choices=STATUS_CHOICES,
                            display_choices=STATUS_DISPLAY_CHOICES,
                            verbose_name=_("Status"),
                            classes=("status",))

    class Meta:
        name = "server_list"
        verbose_name = _("Server List")
        table_actions = (CreateClusterAction,)
        status_columns = ['status']
        #row_class = UpdateRow
        multi_select = False

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

class CreateClusterTable(tables.DataTable):

    server_id = tables.Column("id", verbose_name=_("ID"), classes=('server_id',))
    name = tables.Column("name", verbose_name=_("Name"))
    primary_public_ip = tables.Column("primary_public_ip", verbose_name=_("Management Address"))
    secondary_public_ip = tables.Column("secondary_public_ip",
        verbose_name=_("Public Address"))
    cluster_ip = tables.Column("cluster_ip", verbose_name=_("Cluster Address"))
    zone = tables.Column("zone", classes=("zone",), verbose_name=_("Zone"))
    osds = tables.Column("osds", verbose_name=_("OSDs (Data Drives)"))
    monitor = tables.Column("monitor", verbose_name=_("Monitor"),
        classes=('monitor',))
    mds = tables.Column("mds", verbose_name=_("MDS"))
    rgw = tables.Column("rgw", verbose_name=_("RGW"))
    is_monitor = tables.Column("ismonitor", verbose_name=_("Monitor"), classes=('is_monitor',),
        empty_value=empty_value_maker("checkbox","is_monitor",1), hidden=True)
    is_storage = tables.Column("isstorage", verbose_name=_("Storage"), classes=('is_storage',),
        empty_value=empty_value_maker("checkbox","is_storage",1),hidden=True)
    server_status = tables.Column("status", verbose_name=_("Server Status"), classes=('server_status',))

    class Meta:
        name = "clusteraction"
        verbose_name = _("Server List")
        multi_select = True

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
