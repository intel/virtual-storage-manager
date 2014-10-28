
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

import urllib
from vsmclient import base

class License(base.Resource):
    """"""
    def __repr__(self):
        return "<License: %s>" % self.id

    def delete(self):
        """Delete this vsm."""
        self.manager.delete(self)

    def update(self, **kwargs):
        """Update the display_name or display_description for this vsm."""
        self.manager.update(self, **kwargs)

    def force_delete(self):
        """Delete the specified vsm ignoring its current state.

        :param vsm: The UUID of the vsm to force-delete.
        """
        self.manager.force_delete(self)

class LicenseManager(base.ManagerWithFind):
    """"""
    resource_class = License

    def license_get(self):
        url = '/licenses/license_status_get'
        return self.api.client.get(url)

    def license_create(self, value):
        body = {'value': value}
        url = '/licenses/license_status_create'
        return self.api.client.post(url, body=body)

    def license_update(self, value):
        body = {'value': value}
        url = '/licenses/license_status_update'
        return self.api.client.post(url, body=body)
        
