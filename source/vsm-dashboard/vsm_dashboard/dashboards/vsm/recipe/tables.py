
# Copyright 2014 Intel Corporation, All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the"License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from vsm_dashboard.dashboards.admin.instances.tables import \
        AdminUpdateRow

from horizon import tables
from vsm_dashboard.api import vsm

def get_tenant_name(instance):
    return instance.tenant.name

def get_memory(instance):
    return filesizeformat(instance.flavor.ram * 1024 * 1024)

def get_vcpus(instance):
    return instance.flavor.vcpus

def get_username(instance):
    return instance.user.name

def get_crushset():
    res = {}
    res['crush_ruleset'] = 'test data'
    return "test data"

class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, volume_id):
        volume = vsm.volume_get(request, volume_id)
        if not volume.display_name:
            volume.display_name = volume_id
        return volume

class FlockingInstancesTable(tables.DataTable):
    host = tables.Column("OS-EXT-SRV-ATTR:host", verbose_name=_("Host"))
    tenant = tables.Column(get_tenant_name, verbose_name=_("Tenant"))
    user = tables.Column(get_username, verbose_name=_("user"))
    vcpus = tables.Column(get_vcpus, verbose_name=_("VCPUs"))
    memory = tables.Column(get_memory, verbose_name=_("Memory"))
    #age = tables.Column('age', verbose_name=_("Age"), filters=(timesince,))

    class Meta:
        name = "instances"
        verbose_name = _("Instances")
        row_class = AdminUpdateRow

class CreateStoragePool(tables.LinkAction):
    name = "create pool"
    verbose_name = _("Create Pool")
    url = "horizon:project:volumes:create"
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

class ListRecipeTable(tables.DataTable):
    host = tables.Column(get_crushset, verbose_name=_("Name"))
    tenant = tables.Column(get_crushset, verbose_name=_("ID"))
    user = tables.Column(get_crushset, verbose_name=_("UpdateTime"))
    vcpus = tables.Column(get_crushset, verbose_name=_("Pg_number"))
    memory = tables.Column(get_crushset, verbose_name=_("crush_ruleset"))
    #age = tables.Column('age', verbose_name=_("Age"), filters=(timesince,))

    class Meta:
        name = "recipe"
        verbose_name = _("recipe")
        row_class = AdminUpdateRow
        #row_class = UpdateRow
        table_actions = (CreateStoragePool, DeleteStoragePool,)
        row_actions = (DeleteStoragePool,)
