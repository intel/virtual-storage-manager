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
from vsm.api import xmlutil
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.api.views import license as license_views
from vsm import conductor

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

def make_license(elem, detailed=False):
    elem.set('license_accept')

    if detailed:
        pass

license_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class LicenseTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('license', selector='license')
        make_license(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=license_nsmap)

class LicensesTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('licenses')
        elem = xmlutil.SubTemplateElement(root, 'licenses', selector='licenses')
        make_license(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=license_nsmap)

class LicenseController(wsgi.Controller):
    """The License controller for the OpenStack API."""
    _view_builder_class = license_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.ext_mgr = ext_mgr
        super(LicenseController, self).__init__()

    def license_status_get(self, req):
        context = req.environ['vsm.context']
        ret = self.conductor_api.license_status_get(context)
        #if ret is None:
        #    LOG.error("In vsm api, licenses.py, ret is None")
        #else:
        #    LOG.error("Gao Gao, ret = %s" % ret)
        #    LOG.error("In vsm api, licenses.py, ret is not None")
        return ret

    def license_status_create(self, req, body=None):
        context = req.environ['vsm.context']
    
        #FIXME(fenqian): Hard code for the id, because we only have
        #one item in database.
        kargs = {'id': 1,
                 'license_accept': body['value']}
        ret = self.conductor_api.license_status_create(context, values=kargs)
        return ret

    def license_status_update(self, req, body=None):
        context = req.environ['vsm.context']
        value = body['value']
        ret = self.conductor_api.license_status_update(context, value)
        return ret

def create_resource(ext_mgr):
    return wsgi.Resource(LicenseController(ext_mgr))
