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

"""The storage type & storage types extra specs extension."""

from webob import exc

from vsm.api.openstack import wsgi
from vsm.api.views import types as views_types
from vsm.api import xmlutil
from vsm import exception

def make_voltype(elem):
    elem.set('id')
    elem.set('name')
    extra_specs = xmlutil.make_flat_dict('extra_specs', selector='extra_specs')
    elem.append(extra_specs)

class HardwareTypeTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storage_type', selector='storage_type')
        make_voltype(root)
        return xmlutil.MasterTemplate(root, 1)

class HardwareTypesTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storage_types')
        elem = xmlutil.SubTemplateElement(root, 'storage_type',
                                          selector='storage_types')
        make_voltype(elem)
        return xmlutil.MasterTemplate(root, 1)

class HardwareTypesController(wsgi.Controller):
    """The storage types API controller for the OpenStack API."""

    _view_builder_class = views_types.ViewBuilder

    @wsgi.serializers(xml=HardwareTypesTemplate)
    def index(self, req):
        """Returns the list of storage types."""
        context = req.environ['vsm.context']
        vol_types = storage_types.get_all_types(context).values()
        return self._view_builder.index(req, vol_types)

    @wsgi.serializers(xml=HardwareTypeTemplate)
    def show(self, req, id):
        """Return a single storage type item."""
        context = req.environ['vsm.context']

        try:
            vol_type = storage_types.get_storage_type(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        # TODO(bcwaldon): remove str cast once we use uuids
        vol_type['id'] = str(vol_type['id'])
        return self._view_builder.show(req, vol_type)

def create_resource():
    return wsgi.Resource(HardwareTypesController())
