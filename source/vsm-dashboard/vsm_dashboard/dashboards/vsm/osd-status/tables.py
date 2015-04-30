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

from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict
from django import forms

from django.utils.safestring import mark_safe

from horizon import tables
from horizon.utils import html
from horizon import exceptions
from vsm_dashboard.api import vsm as vsmapi
from .utils import checkbox_transform

STRING_SEPARATOR = "__"

class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, osd_id):
        osd = vsmapi.osd_get(request, osd_id)
        return osd

STATUS_DISPLAY_CHOICES = (
    ("resize", "Resize/Migrate"),
    ("verify_resize", "Confirm or Revert Resize/Migrate"),
    ("revert_resize", "Revert Resize/Migrate"),
)

class ListOSDStatusTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Present", True),
        ("Removed", False),
    )

    #server_id = tables.Column("id", verbose_name=_("ID"))
    ordinal = tables.Column("id", verbose_name=_("ordinal"), hidden=True)
    osd_name = tables.Column("osd_name", verbose_name=_("OSD Name"))
    vsm_status = tables.Column("vsm_status",
                               status=True,
                               status_choices=STATUS_CHOICES,
                               display_choices=STATUS_DISPLAY_CHOICES,
                               verbose_name=_("VSM Status"),)
    osd_state = tables.Column("osd_state", verbose_name=_("OSD Status"))
    crush_weight = tables.Column("crush_weight", verbose_name=_("Crush Weight"))
    capacity_total = tables.Column("capacity_total", verbose_name=_("Capacity Total (MB)"))
    capacity_used = tables.Column("capacity_used", verbose_name=_("Capacity Used (MB)"))
    capacity_avail = tables.Column("capacity_avail", verbose_name=_("Capacity Available (MB)"))
    capacity_percent_used = tables.Column("capacity_percent_used", verbose_name=_("Percent Used Capacity"))
    server = tables.Column("server", verbose_name=_("Server"))
    storage_group = tables.Column("storage_group", verbose_name=_("Storage Group"))
    zone = tables.Column("zone", verbose_name=_("Zone"))
    updated_at = tables.Column("updated_at", verbose_name=_("Updated at"), classes=("span2",))
    pageCount = tables.Column("pageCount", verbose_name=_("pageCount"), classes=("pageCount",),hidden=True)
    pageIndex = tables.Column("pageIndex", verbose_name=_("pageIndex"), classes=("pageIndex",),hidden=True)
    pagerCount = tables.Column("pagerCount", verbose_name=_("pagerCount"), classes=("pagerCount",),hidden=True)
    pagerIndex = tables.Column("pagerIndex", verbose_name=_("pagerIndex"), classes=("pagerIndex",),hidden=True)

    class Meta:
        name = "server_list"
        verbose_name = _("OSD List")
        #status_columns = ['status']
        row_class = UpdateRow
        multi_select = False

    def get_object_id(self, datum):
        if hasattr(datum, "id"):
            return datum.id
        else:
            return datum["id"]


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

