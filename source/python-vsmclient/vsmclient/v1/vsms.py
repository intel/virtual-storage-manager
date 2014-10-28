# Copyright 2011 Denali Systems, Inc.
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

"""
Volume interface (1.1 extension).
"""

import urllib
from vsmclient import base

class Volume(base.Resource):
    """A vsm is an extra block level storage to the OpenStack instances."""
    def __repr__(self):
        try:
            return "<Volume: %s>" % self.id
        except AttributeError:
            return "<VSM: summary>"

    def delete(self):
        """Delete this vsm."""
        self.manager.delete(self)

    def update(self, **kwargs):
        """Update the display_name or display_description for this vsm."""
        self.manager.update(self, **kwargs)

    def attach(self, instance_uuid, mountpoint):
        """Set attachment metadata.

        :param instance_uuid: uuid of the attaching instance.
        :param mountpoint: mountpoint on the attaching instance.
        """
        return self.manager.attach(self, instance_uuid, mountpoint)

    def detach(self):
        """Clear attachment metadata."""
        return self.manager.detach(self)

    def reserve(self, vsm):
        """Reserve this vsm."""
        return self.manager.reserve(self)

    def unreserve(self, vsm):
        """Unreserve this vsm."""
        return self.manager.unreserve(self)

    def begin_detaching(self, vsm):
        """Begin detaching vsm."""
        return self.manager.begin_detaching(self)

    def roll_detaching(self, vsm):
        """Roll detaching vsm."""
        return self.manager.roll_detaching(self)

    def initialize_connection(self, vsm, connector):
        """Initialize a vsm connection.

        :param connector: connector dict from nova.
        """
        return self.manager.initialize_connection(self, connector)

    def terminate_connection(self, vsm, connector):
        """Terminate a vsm connection.

        :param connector: connector dict from nova.
        """
        return self.manager.terminate_connection(self, connector)

    def set_metadata(self, vsm, metadata):
        """Set or Append metadata to a vsm.

        :param type : The :class: `Volume` to set metadata on
        :param metadata: A dict of key/value pairs to set
        """
        return self.manager.set_metadata(self, metadata)

    def upload_to_image(self, force, image_name, container_format,
                        disk_format):
        """Upload a vsm to image service as an image."""
        self.manager.upload_to_image(self, force, image_name, container_format,
                                     disk_format)

    def force_delete(self):
        """Delete the specified vsm ignoring its current state.

        :param vsm: The UUID of the vsm to force-delete.
        """
        self.manager.force_delete(self)

class VolumeManager(base.ManagerWithFind):
    """
    Manage :class:`Volume` resources.
    """
    resource_class = Volume

    def create(self, size, snapshot_id=None, source_volid=None,
               display_name=None, display_description=None,
               vsm_type=None, user_id=None,
               project_id=None, availability_zone=None,
               metadata=None, imageRef=None):
        """
        Create a vsm.

        :param size: Size of vsm in GB
        :param snapshot_id: ID of the snapshot
        :param display_name: Name of the vsm
        :param display_description: Description of the vsm
        :param vsm_type: Type of vsm
        :rtype: :class:`Volume`
        :param user_id: User id derived from context
        :param project_id: Project id derived from context
        :param availability_zone: Availability Zone to use
        :param metadata: Optional metadata to set on vsm creation
        :param imageRef: reference to an image stored in glance
        :param source_volid: ID of source vsm to clone from
        """

        if metadata is None:
            vsm_metadata = {}
        else:
            vsm_metadata = metadata

        body = {'vsm': {'size': size,
                           'snapshot_id': snapshot_id,
                           'display_name': display_name,
                           'display_description': display_description,
                           'vsm_type': vsm_type,
                           'user_id': user_id,
                           'project_id': project_id,
                           'availability_zone': availability_zone,
                           'status': "creating",
                           'attach_status': "detached",
                           'metadata': vsm_metadata,
                           'imageRef': imageRef,
                           'source_volid': source_volid,
                           }}
        return self._create('/vsms', body, 'vsm')

    def get(self, vsm_id):
        """
        Get a vsm.

        :param vsm_id: The ID of the vsm to delete.
        :rtype: :class:`Volume`
        """
        return self._get("/vsms/%s" % vsm_id, "vsm")

    def list(self, detailed=True, search_opts=None):
        """
        Get a list of all vsms.

        :rtype: list of :class:`Volume`
        """
        print ' comes to list'
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

        ret = self._list("/conductor%s%s" % (detail, query_string),
                          "conductor")
        return ret

    def delete(self, vsm):
        """
        Delete a vsm.

        :param vsm: The :class:`Volume` to delete.
        """
        self._delete("/vsms/%s" % base.getid(vsm))

    def update(self, vsm, **kwargs):
        """
        Update the display_name or display_description for a vsm.

        :param vsm: The :class:`Volume` to delete.
        """
        if not kwargs:
            return

        body = {"vsm": kwargs}

        self._update("/vsms/%s" % base.getid(vsm), body)

    def _action(self, action, vsm, info=None, **kwargs):
        """
        Perform a vsm "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/vsms/%s/action' % base.getid(vsm)
        return self.api.client.post(url, body=body)

    def host_status(self, req=None):
        """
        Perform a vsm "action."
        """
        body = {'request': req}
        url = '/conductor/host_status'
        return self.api.client.post(url, body=body)

    def create_storage_pool(self, body):
        """
        create a storage pool
        """
        url = '/storage_pool/create'
        return self.api.client.post(url, body=body)

    def get_storage_group_list(self):
        url = '/storage_pool/get_storage_group_list'
        return self.api.client.get(url)

    def get_pool_size_list(self):
        url = '/storage_pool/get_pool_size_list'
        return self.api.client.get(url)

    def list_storage_pool(self, req=None, search_opts=None):
        """
        Perform a vsm "action."
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        #body = {'request': req}
        url = "/storage_pool/list_storage_pool%s" % (query_string)
        return self.api.client.get(url)

    #serer_api
    def get_server_list(self, req=None):
        """
        host list
        """
        url = "/cluster/servers"
        return self.api.client.get(url)

    def add_servers(self, req=None, opts=None):
        """
        add servers
        """
        url = "/cluster/servers/add"
        return self.api.client.post(url, body=opts)

    def remove_servers(request, opts=None):
        """
        remove servers
        """
        url = "/cluster/servers/del"
        return self.api.client.post(url, body=opts)
   
    #zone_api
    def get_zone_list(self, req=None):
        """
        get zone list
        """
        url = "/cluster/zones"
        return self.api.client.get(url)

    def create_zone(self, req=None, opts=None):
        """
        create a zone
        """
        url = "/cluster/zones/add"
        return self.api.client.post(url, body=opts)

    #cluster list
    def get_cluster_list(self, req=None):
        """
        get cluster list
        """
        url = "/clusters"
        return self.api.client.get(url)

    def create_cluster(self, req=None, opts=None):
        """
        create cluster
        """
        url = "/clusters"
        return self.api.client.post(url, body=opts)

    def resource_info(self, req=None):
        """
        Perform a vsm "action."
        """
        body = {'request': req}
        url = '/conductor/resource_info'
        return self.api.client.post(url, body=body)

    def asm_settings(self, req=None):
        """
        Perform a vsm "action."
        """
        body = {'request': req}
        url = '/conductor/asm_settings'
        return self.api.client.post(url, body=body)

    def initialize_connection(self, vsm, connector):
        """
        Initialize a vsm connection.

        :param vsm: The :class:`Volume` (or its ID).
        :param connector: connector dict from nova.
        """
        return self._action('os-initialize_connection', vsm,
                            {'connector': connector})[1]['connection_info']

    def terminate_connection(self, vsm, connector):
        """
        Terminate a vsm connection.

        :param vsm: The :class:`Volume` (or its ID).
        :param connector: connector dict from nova.
        """
        self._action('os-terminate_connection', vsm,
                     {'connector': connector})

    def summary(self):
        """
        summary
        """
        url = "/vsms/summary"
        return self._get(url, 'vsm-summary')

