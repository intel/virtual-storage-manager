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

LOG = logging.getLogger(__name__)

class AddECProfileAction(tables.LinkAction):
    name = "add_ec_profile"
    verbose_name = _("New")
    url = "/dashboard/vsm/ecprofiles-management/add_ec_profile_view/"
    classes = ('btn-primary',)

class RemoveECProfilesAction(tables.LinkAction):
    name = "remove_ec_profiles"
    verbose_name = _("Remove")
    classes = ('btn-primary',)
    url = "horizon:vsm:ecprofiles-management:index"



class ECProfilesTable(tables.DataTable):
    id = tables.Column("id", verbose_name=_("ID"), hidden=True)
    name = tables.Column("name", verbose_name=_("Name"))
    plugin = tables.Column("plugin", verbose_name=_("Plugin Name"))
    plugin_path = tables.Column("plugin_path", verbose_name=_("Plugin Path"))
    pg_num = tables.Column("pg_num", verbose_name=_("PG Number"))
    k_v_dict = tables.Column("plugin_kv_pair", verbose_name=_("Key Values Pairs"))
    class Meta:
        name = "ec_profiles"
        verbose_name = _("EC Profiles List")
        table_actions = (AddECProfileAction,RemoveECProfilesAction)

    def get_object_id(self, datum):
        if hasattr(datum, "id"):
            return datum.id
        else:
            return datum["id"]
