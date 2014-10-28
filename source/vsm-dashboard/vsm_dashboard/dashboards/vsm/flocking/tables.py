
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

def get_tenant_name(instance):
    return instance.tenant.name

def get_memory(instance):
    return filesizeformat(instance.flavor.ram * 1024 * 1024)

def get_vcpus(instance):
    return instance.flavor.vcpus

def get_username(instance):
    return instance.user.name

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
