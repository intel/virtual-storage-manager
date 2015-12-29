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
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon import exceptions
from horizon import messages
from vsm_dashboard.api import vsm as vsmapi

STRING_SEPARATOR = "__"
LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("Present",)
REMOVED_STATES = ("Removed",)
UNINIT_STATES = ("Uninitialized")

class UpdateRow(tables.Row):
    ajax = False

    def get_data(self, request, osd_id):
        osd = vsmapi.osd_get(request, osd_id)
        return osd

class RestartOsdsAction(tables.LinkAction):
    name = "restart_osds"
    verbose_name = _("Restart")
    classes = ('btn-primary',)
    url = "horizon:vsm:devices-management:index"


class RemoveOsdsAction(tables.LinkAction):
    name = "remove_osds"
    verbose_name = _("Remove")
    classes = ('btn-primary',)
    url = "horizon:vsm:devices-management:index"


class RestoreOsdsAction(tables.LinkAction):
    name = "restore_osds"
    verbose_name = _("Restore")
    classes = ('btn-primary',)
    url = "horizon:vsm:devices-management:index"


class AddOsdsAction(tables.BatchAction):
    name = "Add_osds"
    action_present = _("Add")
    action_past = _("Scheduled add of")
    data_type_singular = _("Osd")
    data_type_plural = _("Osds")
    classes = ('btn-primary',)
    redirect_url = "horizon:vsm:devices-management:index"

    def allowed(self, request, osd=None):
        if osd is not None:
            if osd['vsm_status'] not in UNINIT_STATES:
                msg = _('Only osd with VSM status "%s" will be added'%UNINIT_STATES)
                messages.error(request, msg)
                return False
        return True

    def action(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        name = self.table.get_object_display(obj)
        try:
            vsmapi.add_osd_from_node_in_cluster(request, obj_id)
        except Exception:
            msg = _('Error adding %s.' % name)
            LOG.info(msg)
            redirect = reverse(self.redirect_url)
            exceptions.handle(request, msg, redirect=redirect)

STATUS_DISPLAY_CHOICES = (
    ("removing", "Removing"),
    ("restarting", "Restarting"),
    ("restoring", "Restoring"),
)

class AddOSDAction(tables.LinkAction):
    name = "add_osd"
    verbose_name = _("New")
    url = "/dashboard/vsm/devices-management/add_new_osd/"
    classes = ('btn-primary',)

class OsdsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Present", True),
        ("Removed", False),
    )
    osd = tables.Column("osd", verbose_name=_("OSD"))
    vsm_status = tables.Column("vsm_status",
                               status=True,
                               status_choices=STATUS_CHOICES,
                               display_choices=STATUS_DISPLAY_CHOICES,
                               verbose_name=_("VSM Status"), hidden=True
                               )
    osd_state = tables.Column("osd_state", verbose_name=_("OSD Status"))
    osd_weight = tables.Column("osd_weight", verbose_name=_("OSD Weight"))
    server = tables.Column("server", verbose_name=_("Server"))
    storage_group = tables.Column("storage_group", \
                                  verbose_name=_("Storage Class"))
    zone = tables.Column("zone", verbose_name=_("Zone"))
    data_dev_path = tables.Column("data_dev_path", \
                                  verbose_name=_("Data Device Path"), hidden=True)
    data_dev_status = tables.Column("data_dev_status", \
                                    verbose_name=_("Data Device Status"))
    data_dev_capacity = tables.Column("data_dev_capacity", \
                                      verbose_name=_("Data Device Capacity (MB)"), hidden=True)
    data_dev_used = tables.Column("data_dev_used", \
                                  verbose_name=_("Data Device Used (MB)"), hidden=True)
    data_dev_available = tables.Column("data_dev_available", \
                                       verbose_name=_("Data Device Available (MB)"), hidden=True)
    journal_device_path = tables.Column("journal_device_path", \
                                        verbose_name=_("Journal Device Path"), hidden=True)
    journal_device_status = tables.Column("journal_device_status", \
                                   verbose_name=_("Journal Device Status"))
    full_status = tables.Column("full_status", \
                               verbose_name=_("Used(%)"), hidden=True)
    full_warn = tables.Column("full_warn", \
                               verbose_name=_("Used Wran"), hidden=True)
    capacity_status = tables.Column("capacity_status", \
                                   verbose_name=_("Capacity Status"))

    class Meta:
        name = "osds"
        verbose_name = _("Device List")
        table_actions = (RestartOsdsAction, RemoveOsdsAction,
                         RestoreOsdsAction,AddOSDAction)
        status_columns = ['vsm_status']
        row_class = UpdateRow

    def get_object_id(self, obj):
        return obj["id"]

    def get_object_by_id(self, obj_id):
        for obj in self.data:
            if self.get_object_id(obj) == int(obj_id):
                return obj
        raise ValueError('No match found for the id "%s".' % obj_id)

    def get_object_display(self, obj):
        return obj["osd"]


