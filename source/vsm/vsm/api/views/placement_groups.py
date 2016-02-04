# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Inc.
# All Rights Reserved.
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

from vsm.api import common
import logging

LOG = logging.getLogger(__name__)

class ViewBuilder(common.ViewBuilder):
    _collection_name = "placement_groups"

    def basic(self, request, placement_group):
        LOG.info("placement_groups api view %s " % placement_group)
        return {
            "placement_group": {
                "id": placement_group['id'],
                "pg_id": placement_group['pgid'],
                "state": placement_group['state'],
                "up": placement_group['up'],
                "acting": placement_group['acting'],
            }
        }

    def _detail(self, request, placement_group):
        LOG.info("placement_groups api detail view %s " % placement_group)
        return {
            "placement_group": {
                "id": placement_group['id'],
                "pg_id": placement_group['pgid'],
                "state": placement_group['state'],
                "up": placement_group['up'],
                "acting": placement_group['acting'],
            }
        }

    def detail(self, request, placement_groups):
        return self._list_view(self._detail, request, placement_groups)

    def index(self, request, placement_groups):
        """Show a list of placement_groups without many details."""
        return self._list_view(self.basic, request, placement_groups)

    def _list_view(self, func, request, placement_groups):
        """Provide a view for a list of placement_groups."""
        placement_group_list = [func(request, placement_group)["placement_group"] for placement_group in placement_groups]
        placement_groups_dict = dict(placement_groups=placement_group_list)
        return placement_groups_dict

