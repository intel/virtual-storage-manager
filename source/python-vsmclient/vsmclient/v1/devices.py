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
Devices interface.
"""

import urllib
from vsmclient import base


class Device(base.Resource):
    """A device is a disk on server for osd as data or journal."""
    def __repr__(self):
        return "<Device: %s>" % self.id

class DeviceManager(base.ManagerWithFind):
    """
    Manage :class:`Device` resources.
    """
    resource_class = Device

    def get(self, device_id):
        """
        Get a device.

        :param device_id: The ID of the device.
        :rtype: :class:`Device`
        """
        return self._get("/devices/%s" % device_id, "device")

    def list(self, detailed=False, search_opts=None):
        """
        Get a list of all devices.

        :rtype: list of :class:`Device`
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

        ret = self._list("/devices%s%s" % (detail, query_string),
                         "devices")
        return ret

    def get_available_disks(self, search_opts=None):
        """
        Get a list of available disks
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""
        resp, body = self.api.client.get("/devices/get_available_disks%s" % (query_string))
        body = body.get("available_disks")
        result_mode = search_opts.get('result_mode')
        if result_mode == 'get_disks':
            return {'disks': body}
        ret = {"ret":1}
        message = []
        paths = search_opts.get("path")
        disks = []
        for disk in body:
            disk_name = disk.get('disk_name','')
            by_path = disk.get('by_path','')
            by_uuid = disk.get('by_uuid','')
            if disk_name:
                disks.append(disk_name)
            if by_path:
                disks.append(by_path)
            if by_uuid:
                disks.append(by_uuid)
        if paths:
            unaviable_paths = [path for path in paths if path not in disks]
            if unaviable_paths:
                message.append('There is no %s '%(','.join(unaviable_paths)))
        if message:
            ret = {"ret":0,'message':'.'.join(message)}
        return ret

    def get_smart_info(self, search_opts=None):
        """
        Get a dict of smart info
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""
        resp, body = self.api.client.get("/devices/get_smart_info%s" % (query_string))
        smart_info = body.get("smart_info")
        return smart_info