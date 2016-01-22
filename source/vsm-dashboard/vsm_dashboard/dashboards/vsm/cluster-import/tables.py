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

from django.utils.translation import ugettext_lazy as _
from horizon import tables
STRING_SEPARATOR = "__"

STATUS_DISPLAY_CHOICES = (
    ("resize", "Resize/Migrate"),
    ("verify_resize", "Confirm or Revert Resize/Migrate"),
    ("revert_resize", "Revert Resize/Migrate"),
)

class ImportClusterAction(tables.LinkAction):
    name = "import_cluster"
    verbose_name = _("Import Cluster")
    url = "horizon:vsm:cluster-import:importcluster"
    classes = ("ajax-modal", "btn-primary")

    

class ListServerTable(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("available", True),
        ("Active", True),
    )

    server_id = tables.Column("id", verbose_name=_("ID"))
    name = tables.Column("name", verbose_name=_("Name"))
    primary_public_ip = tables.Column("primary_public_ip", verbose_name=_("Management Address"), attrs={"data-type": "ip"})
    secondary_public_ip = tables.Column("secondary_public_ip", verbose_name=_("Public Address"), attrs={"data-type": "ip"})
    cluster_ip = tables.Column("cluster_ip", verbose_name=_("Cluster Address"), attrs={"data-type": "ip"})
    osds = tables.Column("osds", verbose_name=_("OSDs"))
    is_monitor = tables.Column("is_monitor", verbose_name=_("Monitor"))
    zone = tables.Column("zone", classes=("zone",), verbose_name=_("Zone"))
    status = tables.Column("status", status=True,
                            status_choices=STATUS_CHOICES,
                            display_choices=STATUS_DISPLAY_CHOICES,
                            verbose_name=_("Status"))

    class Meta:
        name = "server_list"
        verbose_name = _("Server List")
        table_actions = (ImportClusterAction,)
        status_columns = ['status']
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

