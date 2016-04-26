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
RGWs interface.
"""

import urllib
from vsmclient import base


class Rgw(base.Resource):
    """"""

    def __repr__(self):
        return "<Rgw: %s>" % self.id

class RgwManager(base.ManagerWithFind):
    """
    Manage :class:`RGW` resources.
    """
    resource_class = Rgw

    def create(self, host, rgw_instance_name="radosgw.gateway", is_ssl=False, uid="johndoe",
               display_name="John Doe", email="john@example.comjohn@example.com",
               sub_user="johndoe:swift", access="full", key_type="swift"):
        """
        Create a rgw.
        :param host:
        :param rgw_instance_name:
        :param is_ssl:
        :param uid:
        :param display_name:
        :param email:
        :param sub_user:
        :param access:
        :param key_type:
        :return:
        """

        body = {
            "rgw": {
                "rgw_info": {
                    "server_name": host,
                    "rgw_instance_name": rgw_instance_name,
                    "is_ssl": is_ssl
                },
                "user_info": {
                    "uid": uid,
                    "display_name": display_name,
                    "email": email,
                    "sub_user": sub_user,
                    "access": access,
                    "key_type": key_type
                }
            }
        }

        return self._create('/rgws', body, 'rgw')