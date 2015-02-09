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
from vsm_dashboard.api import vsm

class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, volume_id):
        volume = vsm.volume_get(request, volume_id)
        if not volume.display_name:
            volume.display_name = volume_id
        return volume

class CreateStoragePool(tables.LinkAction):
    name = "create pool"
    verbose_name = _("Create Replicated Pool")
    url = "horizon:vsm:poolsmanagement:create"
    classes = ("ajax-modal", "btn-create")

class CreateErasureCodedPool(tables.LinkAction):
    name = "create erasure coded pool"
    verbose_name = _("Create EC Pool")
    url = "horizon:vsm:poolsmanagement:create_ec_pool"
    classes = ("ajax-modal", "btn-create")

class AddCacheTier(tables.LinkAction):
    name = "add cache tier"
    verbose_name = _("Add Cache Tier")
    url = "horizon:vsm:poolsmanagement:add_cache_tier"
    classes = ("ajax-modal", "btn-create")

class RemoveCacheTier(tables.LinkAction):
    name = "remove cache tier"
    verbose_name = _("Remove Cache Tier")
    url = "horizon:vsm:poolsmanagement:remove_cache_tier"
    classes = ("ajax-modal", "btn-create")

class DeleteStoragePool(tables.DeleteAction):
    data_type_singular = _("StoragePool")
    data_type_plural = _("StoragePools")
    action_past = _("Scheduled deletion of")

    def delete(self, request, obj_id):
        obj = self.table.get_object_by_id(obj_id)
        name = self.table.get_object_display(obj)
        try:
            vsm.volume_delete(request, obj_id)
        except:
            msg = _('Unable to delete volume "%s". One or more snapshots '
                    'depend on it.')
            exceptions.check_message(["snapshots", "dependent"], msg % name)
            raise

    def allowed(self, request, volume=None):
        if volume:
            return volume.status in DELETABLE_STATES
        return True

class ListPoolTable(tables.DataTable):

    poolId = tables.Column("poolId", verbose_name=_("ID"))
    name = tables.Column("name", verbose_name=_("Name"))
    storageType = tables.Column("storageGroup", verbose_name=_("Primary Storage Group"))
    replicaStorageType = tables.Column("replica_storage_group", verbose_name=_("Replica Storage Group"))
    pgNum = tables.Column("pgNum", verbose_name=_("Placement Group Count"))
    size = tables.Column("size", verbose_name=_("Size"))
    quota = tables.Column("empty", verbose_name=_("Quota (GB)"), empty_value=lambda x: "-" if x["quota"] in (0, None) else x["quota"])
    cache_tier_status = tables.Column("cache_tier_status", verbose_name=_("Cache Tier Status"))
    erasure_code_status = tables.Column("erasure_code_status", verbose_name=_("Erasure Code Status"))
    status = tables.Column("status", verbose_name=_("Status"))
    createdBy = tables.Column("createdBy", verbose_name=_("Created By"))
    tag = tables.Column("tag", verbose_name=_("Tag"))
#    cluster = tables.Column("clusterName", verbose_name=_("Cluster"))

    class Meta:
        name = "pools"
        verbose_name = _("Storage Pools")
        table_actions = (AddCacheTier, RemoveCacheTier, CreateStoragePool, CreateErasureCodedPool)
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
