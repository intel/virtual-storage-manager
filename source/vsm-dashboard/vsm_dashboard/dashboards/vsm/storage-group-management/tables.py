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

class CreateStorageGroupAction(tables.LinkAction):
    name = "create storage group"
    verbose_name = _("Add Storage Group")
    url = "horizon:vsm:storage-group-management:create"
    classes = ("ajax-modal", "btn-primary")

class ListStorageGroupTable(tables.DataTable):

    storage_group_id = tables.Column("id", verbose_name=_("ID"), classes=("storage_group_list",))

    name = tables.Column("name", verbose_name=_("Name"))
    storage_class = tables.Column("storage_class", verbose_name=_("Storage Class"))
    friendly_name = tables.Column("friendly_name", verbose_name=_("Friendly Name"))

    class Meta:
        name = "storage_group_list"
        verbose_name = _("Storage Group List")
        table_actions = (CreateStorageGroupAction, )
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
