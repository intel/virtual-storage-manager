#  Copyright 2014 Intel Corporation, All Rights Reserved.
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

"""
StorageGroups interface.
"""

import urllib
from vsmclient import base


class StorageGroup(base.Resource):
    """"""
    def __repr__(self):
        return "<StorageGroup: %s>" % self.id

class StorageGroupsManager(base.ManagerWithFind):
    """
    Manage :class:`StorageGroup` resources.
    """
    resource_class = StorageGroup

    def create(self, body):

        """
        Create a storage_group.
        """

        #body = {'zone': {'name': name
        #                   }}
        return self._create('/storage_groups', body, 'storage_group')

    def create_with_takes(self, body):

        """
        Create a storage_group with takes and write rule to crushmap.
        """

        #body = {'zone': {'name': name
        #                   }}
        url = "/storage_groups/create_with_takes"
        return self.api.client.post(url,body=body)

    def update_with_takes(self, body):

        """
        update a storage_group with takes in db and update rule in crushmap.
        """

        #body = {'zone': {'name': name
        #                   }}
        url = "/storage_groups/update_with_takes"
        return self.api.client.post(url,body=body)

    def get(self, storage_group_id):
        """
        Get a storage_group.

        :param storage_group_id: The ID of the storage_group.
        :rtype: :class:`StorageGroup`
        """
        return self._get("/storage_groups/%s" % storage_group_id, "storage_group")

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all storage_groups.

        :rtype: list of :class:`StorageGroup`
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        detail = ""
        if detailed:
            detail = "/detail"

        ret = self._list("/storage_groups%s%s" % (detail, query_string),
                          "storage_groups")
        return ret

    def summary(self):
        """
        summary
        """
        url = "/storage_groups/summary"
        return self._get(url, 'storage_group-summary')

    def _action(self, action, storage_group, info=None, **kwargs):
        """
        Perform a storage_group "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/storage_groups/%s/action' % base.getid(storage_group)
        return self.api.client.post(url, body=body)

    def get_default_pg_num(self,search_opts):
        """
        summary
        """
        if search_opts is None:
            search_opts = {}
        storge_group_name = search_opts.get('storage_group_name')
        url = "/storage_groups/get_default_pg_num?storage_group_name=%s"%storge_group_name
        return self.api.client.get(url)