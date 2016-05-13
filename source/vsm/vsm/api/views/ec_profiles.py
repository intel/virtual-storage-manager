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
import time
LOG = logging.getLogger(__name__)

class ViewBuilder(common.ViewBuilder):
    _collection_name = "ec_profiles"
    def _detail(self, request, ec_profile):
        LOG.info("ec_profiles api detail view %s " % ec_profile)
        #LOG.info("snapshot api detail view 2222 %s " % type(snapshot['updated_at']))
        ec_profile = {
                "id": ec_profile.id,
                "name":ec_profile.name,
                "plugin": ec_profile.plugin,
                "plugin_path": ec_profile.plugin_path,
                "pg_num":ec_profile.pg_num,
                "plugin_kv_pair": ec_profile.plugin_kv_pair,
        }

        return ec_profile

    def detail(self, request, ec_profiles):
        LOG.info('ec_profiles detail view-----%s'%ec_profiles)
        return self._list_view(self._detail, request, ec_profiles)



    def _list_view(self, func, request, ec_profiles):
        """Provide a view for a list of ec_profiles."""
        ec_profile_list = [func(request, ec_profile) for ec_profile in ec_profiles]
        ec_profile_dict = dict(ec_profiles=ec_profile_list)
        return ec_profile_dict