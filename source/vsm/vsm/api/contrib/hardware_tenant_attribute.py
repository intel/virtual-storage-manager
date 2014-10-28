#   Copyright 2012 OpenStack, LLC.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

from vsm.api import extensions
from vsm.api.openstack import wsgi
from vsm.api import xmlutil
from vsm import storage

authorize = extensions.soft_extension_authorizer('storage',
                                                 'storage_tenant_attribute')

class HardwareTenantAttributeController(wsgi.Controller):
    def __init__(self, *args, **kwargs):
        super(HardwareTenantAttributeController, self).__init__(*args, **kwargs)
        self.storage_api = storage.API()

    def _add_storage_tenant_attribute(self, context, resp_storage):
        try:
            db_storage = self.storage_api.get(context, resp_storage['id'])
        except Exception:
            return
        else:
            key = "%s:tenant_id" % Hardware_tenant_attribute.alias
            resp_storage[key] = db_storage['project_id']

    @wsgi.extends
    def show(self, req, resp_obj, id):
        context = req.environ['vsm.context']
        if authorize(context):
            resp_obj.attach(xml=HardwareTenantAttributeTemplate())
            self._add_storage_tenant_attribute(context, resp_obj.obj['storage'])

    @wsgi.extends
    def detail(self, req, resp_obj):
        context = req.environ['vsm.context']
        if authorize(context):
            resp_obj.attach(xml=HardwareListTenantAttributeTemplate())
            for storage in list(resp_obj.obj['storages']):
                self._add_storage_tenant_attribute(context, storage)

class Hardware_tenant_attribute(extensions.ExtensionDescriptor):
    """Expose the internal project_id as an attribute of a storage."""

    name = "HardwareTenantAttribute"
    alias = "os-vol-tenant-attr"
    namespace = ("http://docs.openstack.org/storage/ext/"
                 "storage_tenant_attribute/api/v1")
    updated = "2011-11-03T00:00:00+00:00"

    def get_controller_extensions(self):
        controller = HardwareTenantAttributeController()
        extension = extensions.ControllerExtension(self, 'storages', controller)
        return [extension]

def make_storage(elem):
    elem.set('{%s}tenant_id' % Hardware_tenant_attribute.namespace,
             '%s:tenant_id' % Hardware_tenant_attribute.alias)

class HardwareTenantAttributeTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storage', selector='storage')
        make_storage(root)
        alias = Hardware_tenant_attribute.alias
        namespace = Hardware_tenant_attribute.namespace
        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})

class HardwareListTenantAttributeTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storages')
        elem = xmlutil.SubTemplateElement(root, 'storage', selector='storages')
        make_storage(elem)
        alias = Hardware_tenant_attribute.alias
        namespace = Hardware_tenant_attribute.namespace
        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})
