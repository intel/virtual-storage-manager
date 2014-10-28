# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Openstack, LLC
# Copyright 2012 Nebula, Inc.
# Copyright (c) 2012 X.commerce, a business unit of eBay Inc.
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
import json
from django.core.urlresolvers import reverse
from django.template.defaultfilters import filesizeformat
from django.template.defaultfilters import title
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict
from django import shortcuts
from django import forms

from django.utils.safestring import mark_safe

from horizon import tables
from horizon.utils import filters
from horizon.utils import html
from horizon import exceptions
from horizon import messages
from vsm_dashboard.api import vsm as vsmapi

STRING_SEPARATOR = "__"
LOG = logging.getLogger(__name__)

ACTIVE_STATES = ("Present",)
REMOVED_STATES = ("Removed",)

class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, osd_id):
        osd = vsmapi.osd_get(request, osd_id)
        return osd

class RestartOsdsAction(tables.BatchAction):
    name = "restart_osds"
    action_present = _("Restart")
    action_past = _("Scheduled restart of")
    data_type_singular = _("Osd")
    data_type_plural = _("Osds")
    classes = ('btn-danger',)
    redirect_url = "horizon:vsm:devices-management:index"

    def allowed(self, request, osd=None):
        if osd is not None:
            if osd['vsm_status'] not in ACTIVE_STATES:
                msg = _('Only osd with VSM status "Present" will be restarted')
                messages.error(request, msg)
                return False
        return True

    def action(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        name = self.table.get_object_display(obj)
        try:
            vsmapi.osd_restart(request, obj_id)
        except Exception:
            msg = _('Error restarting %s.' % name)
            LOG.info(msg)
            redirect = reverse(self.redirect_url)
            exceptions.handle(request, msg, redirect=redirect)

class RemoveOsdsAction(tables.DeleteAction):
    name = "remove_osds"
    action_present = _("Remove")
    action_past = _("Removed")
    data_type_singular = _("Osd")
    data_type_plural = _("Osds")
    redirect_url = "horizon:vsm:devices-management:index"

    def allowed(self, request, osd=None):
        if osd is not None:
            if osd['vsm_status'] not in ACTIVE_STATES:
                msg = _('Only osd with VSM status "Present" will be removed')
                messages.error(request, msg)
                return False
        return True

    def delete(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        name = self.table.get_object_display(obj)
        try:
            vsmapi.osd_remove(request, obj_id)
        except Exception:
            msg = _('Error deleting %s.' % name)
            LOG.info(msg)
            redirect = reverse(self.redirect_url)
            exceptions.handle(request, msg, redirect=redirect)

class RestoreOsdsAction(tables.BatchAction):
    name = "restore_osds"
    action_present = _("Restore")
    action_past = _("Restored")
    data_type_singular = _("Osd")
    data_type_plural = _("Osds")
    classes = ('btn-danger',)
    redirect_url = "horizon:vsm:devices-management:index"

    def allowed(self, request, osd=None):
        if osd is not None:
            if osd['vsm_status'] not in REMOVED_STATES:
                msg = _('Only osd with VSM status "Removed" will be restored')
                messages.error(request, msg)
                return False
        return True

    def action(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        name = self.table.get_object_display(obj)
        try:
            vsmapi.osd_restore(request, obj_id)
        except Exception:
            msg = _('Error restoring %s.' % name)
            LOG.info(msg)
            redirect = reverse(self.redirect_url)
            exceptions.handle(request, msg, redirect=redirect)

STATUS_DISPLAY_CHOICES = (
    ("removing", "Removing"),
    ("restarting", "Restarting"),
    ("restoring", "Restoring"),
)

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
                               verbose_name=_("VSM Status"),
                               )
    osd_state = tables.Column("osd_state", verbose_name=_("OSD Status"))
    osd_weight = tables.Column("osd_weight", verbose_name=_("OSD Weight"))
    server = tables.Column("server", verbose_name=_("Server"))
    storage_group = tables.Column("storage_group", \
                                  verbose_name=_("Storage Class"))
    zone = tables.Column("zone", verbose_name=_("Zone"))
    data_dev_path = tables.Column("data_dev_path", \
                                  verbose_name=_("Data Device Path"))
    data_dev_status = tables.Column("data_dev_status", \
                                    verbose_name=_("Data Device Status"))
    data_dev_capacity = tables.Column("data_dev_capacity", \
                                      verbose_name=_("Data Device Capacity (MB)"))
    data_dev_used = tables.Column("data_dev_used", \
                                  verbose_name=_("Data Device Used (MB)"))
    data_dev_available = tables.Column("data_dev_available", \
                                       verbose_name=_("Data Device Available (MB)"))
    journal_device_path = tables.Column("journal_device_path", \
                                        verbose_name=_("Journal Device Path"))
    journal_device_status = tables.Column("journal_device_status", \
                                   verbose_name=_("Journal Device Status"))

    class Meta:
        name = "osds"
        verbose_name = _("Device List")
        table_actions = (RestartOsdsAction, RemoveOsdsAction, \
                         RestoreOsdsAction)
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

