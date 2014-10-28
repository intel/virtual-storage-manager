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

"""The Hardware Image Metadata API extension."""

from vsm.api import extensions
from vsm.api.openstack import wsgi
from vsm.api import xmlutil
from vsm import storage

authorize = extensions.soft_extension_authorizer('storage',
                                                 'storage_image_metadata')

class HardwareImageMetadataController(wsgi.Controller):
    def __init__(self, *args, **kwargs):
        super(HardwareImageMetadataController, self).__init__(*args, **kwargs)
        self.storage_api = storage.API()

    def _add_image_metadata(self, context, resp_storage):
        try:
            image_meta = self.storage_api.get_storage_image_metadata(
                context, resp_storage)
        except Exception:
            return
        else:
            if image_meta:
                resp_storage['storage_image_metadata'] = dict(
                    image_meta.iteritems())

    @wsgi.extends
    def show(self, req, resp_obj, id):
        context = req.environ['vsm.context']
        if authorize(context):
            resp_obj.attach(xml=HardwareImageMetadataTemplate())
            self._add_image_metadata(context, resp_obj.obj['storage'])

    @wsgi.extends
    def detail(self, req, resp_obj):
        context = req.environ['vsm.context']
        if authorize(context):
            resp_obj.attach(xml=HardwaresImageMetadataTemplate())
            for storage in list(resp_obj.obj.get('storages', [])):
                self._add_image_metadata(context, storage)

class Hardware_image_metadata(extensions.ExtensionDescriptor):
    """Show image metadata associated with the storage"""

    name = "HardwareImageMetadata"
    alias = "os-vol-image-meta"
    namespace = ("http://docs.openstack.org/storage/ext/"
                 "storage_image_metadata/api/v1")
    updated = "2012-12-07T00:00:00+00:00"

    def get_controller_extensions(self):
        controller = HardwareImageMetadataController()
        extension = extensions.ControllerExtension(self, 'storages', controller)
        return [extension]

class HardwareImageMetadataMetadataTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storage_image_metadata',
                                       selector='storage_image_metadata')
        elem = xmlutil.SubTemplateElement(root, 'meta',
                                          selector=xmlutil.get_items)
        elem.set('key', 0)
        elem.text = 1

        return xmlutil.MasterTemplate(root, 1)

class HardwareImageMetadataTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storage', selector='storage')
        root.append(HardwareImageMetadataMetadataTemplate())

        alias = Hardware_image_metadata.alias
        namespace = Hardware_image_metadata.namespace

        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})

class HardwaresImageMetadataTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storages')
        elem = xmlutil.SubTemplateElement(root, 'storage', selector='storage')
        elem.append(HardwareImageMetadataMetadataTemplate())

        alias = Hardware_image_metadata.alias
        namespace = Hardware_image_metadata.namespace

        return xmlutil.SlaveTemplate(root, 1, nsmap={alias: namespace})
