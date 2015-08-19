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

STRING_SEPARATOR = "__"


class ListServerTable(tables.DataTable):
    server_id = tables.Column("id", verbose_name=_("ID"))
    name = tables.Column("name", verbose_name=_("Name"))
    m_address = tables.Column("m_address", verbose_name=_("M-Address"), attrs={"data-type": "ip"})
    c_address = tables.Column("c_address", verbose_name=_("C-Address"), attrs={"data-type": "ip"})
    osds = tables.Column("osds", verbose_name=_("OSDs"))
    is_monitor = tables.Column("is_monitor", verbose_name=_("Monitor"))
    zone = tables.Column("zone", classes=("zone",), verbose_name=_("Zone"))
    status = tables.Column("status", verbose_name=_("Status"))

    class Meta:
        name = "server_list"
        verbose_name = _("Server List")
        multi_select = False

