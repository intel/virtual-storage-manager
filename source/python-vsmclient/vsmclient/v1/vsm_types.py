# Copyright (c) 2011 Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Volume Type interface.
"""

from vsmclient import base

class VolumeType(base.Resource):
    """
    A Volume Type is the type of vsm to be created
    """
    def __repr__(self):
        return "<VolumeType: %s>" % self.name

    def get_keys(self):
        """
        Get extra specs from a vsm type.

        :param vol_type: The :class:`VolumeType` to get extra specs from
        """
        _resp, body = self.manager.api.client.get(
            "/types/%s/extra_specs" %
            base.getid(self))
        return body["extra_specs"]

    def set_keys(self, metadata):
        """
        Set extra specs on a vsm type.

        :param type : The :class:`VolumeType` to set extra spec on
        :param metadata: A dict of key/value pairs to be set
        """
        body = {'extra_specs': metadata}
        return self.manager._create(
            "/types/%s/extra_specs" % base.getid(self),
            body,
            "extra_specs",
            return_raw=True)

    def unset_keys(self, keys):
        """
        Unset extra specs on a volue type.

        :param type_id: The :class:`VolumeType` to unset extra spec on
        :param keys: A list of keys to be unset
        """

        # NOTE(jdg): This wasn't actually doing all of the keys before
        # the return in the loop resulted in ony ONE key being unset.
        # since on success the return was NONE, we'll only interrupt the loop
        # and return if there's an error
        resp = None
        for k in keys:
            resp = self.manager._delete(
                "/types/%s/extra_specs/%s" % (
                base.getid(self), k))
            if resp is not None:
                return resp

class VolumeTypeManager(base.ManagerWithFind):
    """
    Manage :class:`VolumeType` resources.
    """
    resource_class = VolumeType

    def list(self):
        """
        Get a list of all vsm types.

        :rtype: list of :class:`VolumeType`.
        """
        return self._list("/types", "vsm_types")

    def get(self, vsm_type):
        """
        Get a specific vsm type.

        :param vsm_type: The ID of the :class:`VolumeType` to get.
        :rtype: :class:`VolumeType`
        """
        return self._get("/types/%s" % base.getid(vsm_type), "vsm_type")

    def delete(self, vsm_type):
        """
        Delete a specific vsm_type.

        :param vsm_type: The ID of the :class:`VolumeType` to get.
        """
        self._delete("/types/%s" % base.getid(vsm_type))

    def create(self, name):
        """
        Create a vsm type.

        :param name: Descriptive name of the vsm type
        :rtype: :class:`VolumeType`
        """

        body = {
            "vsm_type": {
                "name": name,
            }
        }

        return self._create("/types", body, "vsm_type")
