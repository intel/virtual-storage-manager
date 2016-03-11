# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Inc.
# All Rights Reserved.

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

"""The rgws api."""


from vsm.api.openstack import wsgi
from vsm.api.views import mdses as mds_views
from vsm import conductor
from vsm import exception
from vsm import flags
from vsm.openstack.common import log as logging
from vsm import scheduler

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS


class RgwController(wsgi.Controller):
    """The rgw API controller for the VSM API."""
    _view_builder_class = mds_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        super(RgwController, self).__init__()

    def create(self, req, body):
        """
        Create a rgw.
        :param req:
        :param body:
        {
            "rgw": {
                "rgw_info": {
                    "server_name": "rgw-node1",
                    "rgw_instance_name": "gateway",
                    "is_ssl": False
                },
                "user_info": {
                    "uid": "johndoe",
                    "display_name": "John Doe",
                    "email": "john@example.comjohn@example.com",
                    "sub_user": "johndoe:swift",
                    "access": "full",
                    "key_type": "swift"
                }
            }
        }
        :return:
        """
        LOG.info("===========================rgw")
        context = req.environ['vsm.context']

        rgw = body['rgw']
        rgw_info = rgw['rgw_info']
        user_info = rgw['user_info']
        server_name = rgw_info.get('server_name', '')
        if not server_name:
            LOG.error("No server to create rgw.")
            raise exception.VsmException()
        rgw_instance_name = rgw_info.get('rgw_instance_name', '')
        if not rgw_instance_name:
            rgw_instance_name = "gateway"
            LOG.warn("rgw instance name uses default name 'rgw'")
        is_ssl = rgw_info.get('is_ssl', '')
        if is_ssl == '':
            is_ssl = False
            LOG.warn("do not use ssl")
        uid = user_info.get('uid') if user_info.get('uid', '') else "johndoe"
        display_name = user_info.get('display_name') if user_info.get('display_name', '') else "John Doe"
        email = user_info.get('email') if user_info.get('email', '') else "john@example.comjohn@example.com"
        sub_user = user_info.get('sub_user') if user_info.get('sub_user', '') else "johndoe:swift"
        access = user_info.get('access') if user_info.get('access', '') else "full"
        key_type = user_info.get('key_type') if user_info.get('key_type', '') else "swift"

        LOG.info("==========server_name: %s" % str(server_name))
        LOG.info("==========rgw_instance_name: %s" % str(rgw_instance_name))
        LOG.info("==========is_ssl: %s" % str(is_ssl))
        LOG.info("==========uid: %s" % str(uid))
        LOG.info("==========display_name: %s" % str(display_name))
        LOG.info("==========email: %s" % str(email))
        LOG.info("==========sub_user: %s" % str(sub_user))
        LOG.info("==========access: %s" % str(access))
        LOG.info("==========key_type: %s" % str(key_type))
        self.scheduler_api.rgw_create(context, server_name, rgw_instance_name, is_ssl,
                                      uid, display_name, email, sub_user, access, key_type)


def create_resource(ext_mgr):
    return wsgi.Resource(RgwController(ext_mgr))
