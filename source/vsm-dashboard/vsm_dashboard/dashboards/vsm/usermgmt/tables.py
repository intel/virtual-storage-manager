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

from django.utils.translation import ugettext_lazy as _

from horizon import tables

from vsm_dashboard import api

STRING_SEPARATOR = "__"
LOG = logging.getLogger(__name__)

class DeleteUser(tables.BatchAction):
    name = "delete_user"
    action_present = _("Delete")
    action_past = _("Deleted")
    data_type_singular = _("User")
    data_type_plural = _("Users")
    classes = ('btn-delete',)

    def allowed(self, request, user=None):
        return (user['name'] != "admin")

    def action(self, request, obj_id):
        api.keystone.user_delete(request, obj_id)

class DisableUser(tables.BatchAction):
    name = "disable_user"
    action_present = ("Disable")
    action_past = ("Disabled")
    data_type_singular = _("User")
    data_type_plural = _("Users")
    classes = ('btn-disable')

    def allowed(self, request, user):
        return (user['name'] != "admin" and user['enabled'])

    def action(self, request, obj_id):
        api.keystone.user_update_enabled(request, obj_id, enabled=False)

class EnableUser(tables.BatchAction):
    name = "enable_user"
    action_present = ("Enable")
    action_past = ("Enabled")
    data_type_singular = _("User")
    data_type_plural = _("Users")
    classes = ('btn-enable')

    def allowed(self, request, user):
        return (user['name'] != "admin" and (not user['enabled']))

    def action(self, request, obj_id):
        api.keystone.user_update_enabled(request, obj_id, enabled=True)

class EditUser(tables.LinkAction):
    name = "edit"
    verbose_name = _("Change Password")
    url = "horizon:vsm:usermgmt:update"
    classes = ("ajax-modal", "btn-primary")

    def allowed(self, request, user):
        return api.keystone.keystone_can_edit_user()

class CreateUserAction(tables.LinkAction):
    name = "create user"
    verbose_name = _("Create User")
    url = "horizon:vsm:usermgmt:create"
    classes = ("ajax-modal", "btn-primary")

    def allowed(self, request, datum):
        return (request.user.username == "admin")  

class UserSettingAction(tables.LinkAction):
    name = "set"
    verbose_name = _("Setting")
    url = "horizon:vsm:usermgmt:setting"
    classes = ("ajax-modal", "btn-primary")


class ListUserTable(tables.DataTable):

    user_id = tables.Column("id", verbose_name=_("ID"), classes=("user_list",),hidden=True)
    name = tables.Column("name", verbose_name=_("Name"))
    email = tables.Column("email", verbose_name=_("Email"), hidden=True)
    enabled = tables.Column("enabled", verbose_name="Enabled", hidden=True)

    class Meta:
        name = "user_list"
        verbose_name = _("User List")
        table_actions = (CreateUserAction,)
        row_actions = (EditUser, DeleteUser)
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
