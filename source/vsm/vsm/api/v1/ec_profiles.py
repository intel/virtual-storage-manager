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


from vsm.api.openstack import wsgi
from vsm import flags


from vsm import scheduler
from vsm import db
from vsm.api.views import ec_profiles as ec_profile_views
from vsm.api import xmlutil
from vsm.openstack.common import log as logging
LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_ec_profile(elem, detailed=False):
    elem.set('id')
    elem.set('name')
    elem.set('plugin')
    elem.set('plugin')
    elem.set('plugin_path')
    elem.set('plugin_kv_pair')
    elem.set('pg_num')
    if detailed:
        pass
ec_profile_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}



class ECProfilesTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('ec_profiles')
        elem = xmlutil.SubTemplateElement(root, 'ec_profiles', selector='ec_profile')
        make_ec_profile(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=ec_profile_nsmap)


class ECProfileController(wsgi.Controller):
    """The ECProfile API controller for the ECProfile API."""
    _view_builder_class = ec_profile_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        super(ECProfileController, self).__init__()

    def detail(self, req):
        """Returns the list of ecprofiles."""
        LOG.info("Get a list of ecprofiles")
        context = req.environ['vsm.context']
        ec_profiles = db.ec_profile_get_all(context)
        return self._view_builder.detail(req, ec_profiles)

    def ec_profile_create(self, req, body=None):
        LOG.info('CEPH_LOG ec_profile_create body %s ' % body)
        context = req.environ['vsm.context']
        for profile in body.get('ec_profiles'):
            db.ec_profile_update_or_create(context,profile)
        return {'message':{'error_code':'','error_msg':'','info':'Add rbd group success!'}}

    def ec_profile_update(self, req, body=None):
        LOG.info('CEPH_LOG ec_profile_update body %s ' % body)
        context = req.environ['vsm.context']
        for profile in body.get('ec_profiles'):
            db.ec_profile_update_or_create(context,profile)
        return {'message':{'error_code':'','error_msg':'','info':'Add rbd group success!'}}


    def ec_profiles_remove(self, req, body=None):
        LOG.info('CEPH_LOG rbd_group_remove body %s ' % body)
        context = req.environ['vsm.context']
        message = {'message':{'error_code':'','error_msg':'','info':''}}
        success_ids = []
        for profile_id in body.get('ec_profiles'):
            db.ec_profile_remove(context,profile_id)
            success_ids.append(profile_id)
        message['message']['info'] += 'EC profiles %s removed success!'%(','.join(success_ids))
        return message


def create_resource(ext_mgr):
    return wsgi.Resource(ECProfileController(ext_mgr))

