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

from vsm_dashboard.api import vsm as vsmapi

LOG = logging.getLogger(__name__)

class AddOpenstackEndpointAction(tables.LinkAction):
    name = "add openstack endpoint"
    verbose_name = _("Add OpenStack Endpoint")
    url = "horizon:vsm:openstackconnect:create"
    classes = ("ajax-modal", "btn-primary")

    def allowed(self, request, datum):
        # return not len(vsmapi.appnode_list(request))
        return True

class DelOpenstackEndpointAction(tables.DeleteAction):
    data_type_singular = ("IP")
    data_type_plural = ("IPs")
    classes = ("btn-delopenstackip",)

    # TODO delete openstack endpoint
    def allowed(self, request, datum):
        return False

    def delete(self, request, obj_id):
        LOG.info("CEPH_LOG DELOPENSTACKIP: DELETE %s" % obj_id)
        vsmapi.del_appnode(request, obj_id)

class EditOpenstackEndpointAction(tables.LinkAction):
    name = "edit openstack endpoint"
    verbose_name = _("Edit")
    url = "horizon:vsm:openstackconnect:update"
    classes = ("ajax-modal", "btn-primary")

    def allowed(self, request, datum):
        return len([x for x in vsmapi.pool_usages(request) if x.attach_status=="success"]) == 0

class ListOpenstackEndpointTable(tables.DataTable):

    id = tables.Column("id", verbose_name=_("ID"), classes=("ip_list",), hidden=True)
    os_tenant_name = tables.Column("os_tenant_name", verbose_name=_("Tenant Name"))
    os_username = tables.Column("os_username", verbose_name=_("UserName"))
    os_password = tables.Column("os_password", verbose_name=_("Password"), hidden=True)
    os_auth_url = tables.Column("os_auth_url", verbose_name=_("Auth Url"))
    os_region_name = tables.Column("os_region_name", verbose_name=_("Region Name"))
    ssh_user = tables.Column("ssh_user", verbose_name=_("SSH User Name"))
    ssh_status = tables.Column("ssh_status", verbose_name=_("Connection Status"))
    log_info = tables.Column("log_info", verbose_name=_("LOG INFO"))

    class Meta:
        name = "openstack_ip_list"
        verbose_name = _("Manage Openstack Access")
        table_actions = (AddOpenstackEndpointAction, DelOpenstackEndpointAction)
        row_actions = (EditOpenstackEndpointAction,)

    def get_object_id(self, datum):
        if hasattr(datum, "id"):
            return datum.id
        else:
            return datum["id"]
