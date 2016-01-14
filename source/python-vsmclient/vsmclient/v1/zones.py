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
Zone interface (1.1 extension).
"""

import urllib
from vsmclient import base
import logging

LOG = logging.getLogger(__name__)

class Zone(base.Resource):
    """A vsm is an extra block level storage to the OpenStack instances."""
    def __repr__(self):
        return "<Zone: %s>" % self.id

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

        :param type : The :class: `Zone` to set metadata on
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

class ZoneManager(base.ManagerWithFind):
    """
    Manage :class:`Zone` resources.
    """
    resource_class = Zone

    def create(self, body):
               
        """
        Create a zone.
        """

        #body = {'zone': {'name': name
        #                   }}
        LOG.debug("DEBUG in vsmclient create zones %s" % str(body))
        return self._create('/zones', body, 'zone')

    def get(self, vsm_id):
        """
        Get a vsm.

        :param vsm_id: The ID of the vsm to delete.
        :rtype: :class:`Zone`
        """
        return self._get("/zones/%s" % vsm_id, "zone")

    def osd_locations_choices(self):
        """
        :rtype: :class:`Zone`
        """
        resp,body = self.api.client.get("/zones/osd_locations_choices")
        return body

    def get_zone_not_in_crush_list(self):
        """
        :rtype: :class:`Zone`
        """
        resp,body = self.api.client.get("/zones/get_zone_not_in_crush_list")
        return body

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all vsms.

        :rtype: list of :class:`Zone`
        """
        #print ' comes to list'
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

        ret = self._list("/zones%s%s" % (detail, query_string),
                          "zones")
        return ret

    def delete(self, vsm):
        """
        Delete a vsm.

        :param vsm: The :class:`Zone` to delete.
        """
        self._delete("/zones/%s" % base.getid(vsm))

    def update(self, vsm, **kwargs):
        """
        Update the display_name or display_description for a vsm.

        :param vsm: The :class:`Zone` to delete.
        """
        if not kwargs:
            return

        body = {"zone": kwargs}

        self._update("/zones/%s" % base.getid(vsm), body)

    def _action(self, action, vsm, info=None, **kwargs):
        """
        Perform a vsm "action."
        """
        body = {action: info}
        self.run_hooks('modify_body_for_action', body, **kwargs)
        url = '/zones/%s/action' % base.getid(vsm)
        return self.api.client.post(url, body=body)

    def add_zone_to_crushmap_and_db(self,body):
        url = '/zones/add_zone_to_crushmap_and_db'
        return self.api.client.post(url, body=body)

    def initialize_connection(self, vsm, connector):
        """
        Initialize a vsm connection.

        :param vsm: The :class:`Zone` (or its ID).
        :param connector: connector dict from nova.
        """
        return self._action('os-initialize_connection', vsm,
                            {'connector': connector})[1]['connection_info']

    def terminate_connection(self, vsm, connector):
        """
        Terminate a vsm connection.

        :param vsm: The :class:`Zone` (or its ID).
        :param connector: connector dict from nova.
        """
        self._action('os-terminate_connection', vsm,
                     {'connector': connector})
