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

#from vsm_dashboard.dashboards.admin.instances.tables import \
#        AdminUpdateRow

from horizon import tables
from horizon import messages
from vsm_dashboard.api import vsm as vsmapi
import logging
LOG = logging.getLogger(__name__)

class PresentPoolAction(tables.BatchAction):
    name = "presentpools"
    action_present = _("Add Pool to OpenStack")
    action_past = _("Scheduled Present Pools")
    data_type_singular = ("Pool")
    data_type_plural = ("")
    classes = ("btn-presentpools",)

    def allowed(self, request, datum):
        LOG.error("CEPH_LOG PRESENTPOOL: ALLOW <")
        LOG.error("CEPH_LOG PRESENTPOOL: datum %s" % datum)
        if datum:
            for data in self.table.data:
                if not (data['status'] in ("running", "whatever")):
                    raise ValueError("Some Pools' status is not correct!")

            appnodes = vsmapi.appnode_list(request)
            if len(appnodes) < 1:
                raise ValueError("No Openstack Node!!")

            for appnode in appnodes:
                if appnode.ssh_status != "reachable":
                    messages.error(request, "Can't SSH to AppNode %s" % appnode.ip)
                    raise Exception("abc")

            if datum['status'] not in ("running", "whatever"):
                raise ValueError("Pool %s status is not correct!" % datum['name'])

            pool_usages = vsmapi.pool_usages(request)
            if datum['id'] in [str(p.pool_id) for p in pool_usages]:
                raise ValueError("Pool %s already Connected to Openstack" % datum['name'])

        LOG.error("CEPH_LOG PRESENTPOOL: ALLOW >")
        return True

    def action(self, request, obj_id):
        LOG.error("CEPH_LOG PRESENTPOOL: ACTION")
        LOG.error(obj_id)
        data = self.table.get_object_by_id(obj_id)
        LOG.error(data)
        LOG.error("CEPH_LOG PRESENTPOOL: ACTION >")
        vsmapi.present_pool(request, [obj_id,])
        messages.success(request, "Present Pool %s Success" % data['name'])

class PresentPoolAction(tables.LinkAction):
    name = "present pools"
    verbose_name = _("Present Pools")
    url = "horizon:vsm:rbdpools:presentpoolsview"
    classes = ("ajax-modal", "btn-create")

    def allowed(self, request, datum):
        LOG.error("CEPH_LOG PRESENTPOOL: ALLOW <")
        LOG.error("CEPH_LOG PRESENTPOOL: datum %s" % datum)
        if datum:
            for data in self.table.data:
                if not (data['status'] in ("running", "whatever")):
                    raise ValueError("Some Pools' status is not correct!")

            appnodes = vsmapi.appnode_list(request)
            if len(appnodes) < 1:
                raise ValueError("No Openstack Node!!")

            for appnode in appnodes:
                if appnode.ssh_status != "reachable":
                    messages.error(request, "Can't SSH to AppNode %s" % appnode.ip)
                    raise Exception("abc")

            if datum['status'] not in ("running", "whatever"):
                raise ValueError("Pool %s status is not correct!" % datum['name'])

            pool_usages = vsmapi.pool_usages(request)
            if datum['id'] in [str(p.pool_id) for p in pool_usages]:
                raise ValueError("Pool %s already Connected to Openstack" % datum['name'])

        LOG.error("CEPH_LOG PRESENTPOOL: ALLOW >")
        return True

class ListPoolTable(tables.DataTable):

    id = tables.Column("id", verbose_name=_("ID"))
    name = tables.Column("name", verbose_name=_("Name"))
    storageType = tables.Column("storageGroup", verbose_name=_("Primary Storage Group"))
    pgNum = tables.Column("pgNum", verbose_name=_("Placement Group Count"))
    size = tables.Column("size", verbose_name=_("Size"))
    status = tables.Column("status", verbose_name=_("Status"))
    createdBy = tables.Column("createdBy", verbose_name=_("Created By"))
    tag = tables.Column("tag", verbose_name=_("Tag"))
    attach_status = tables.Column("attach_status", verbose_name=_("Attach Status"))
#    cluster = tables.Column("clusterName", verbose_name=_("Cluster"))

    class Meta:
        name = "pools"
        verbose_name = _("Manage Openstack RBD Pools")
        table_actions = (PresentPoolAction, )
        #row_actions = (PresentPoolAction,)
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

class ListPresentPoolTable(tables.DataTable):

    id = tables.Column("id", verbose_name=_("ID"), classes=("pool_id",))
    name = tables.Column("name", verbose_name=_("Name"))
    storageType = tables.Column("storageGroup", verbose_name=_("Storage Group"))
    pgNum = tables.Column("pgNum", verbose_name=_("Placement Group Count"))
    size = tables.Column("size", verbose_name=_("Replication Factor"))
    status = tables.Column("status", verbose_name=_("Status"))
    createdBy = tables.Column("createdBy", verbose_name=_("Created By"))
    tag = tables.Column("tag", verbose_name=_("Tag"))
    attach_status = tables.Column("attach_status", verbose_name=_("Attach Status"))
#    cluster = tables.Column("clusterName", verbose_name=_("Cluster"))

    class Meta:
        name = "poolsaction"
        verbose_name = _("Present RBD Pools")
        #row_actions = (PresentPoolAction,)
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
