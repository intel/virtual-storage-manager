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
from vsm.api.views import devices as devices_views
from vsm import conductor,db
from vsm import scheduler

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_device(elem, detailed=False):
    elem.set('id')
    elem.set('name')
    elem.set('path')
    elem.set('journal')
    elem.set('total_capacity_kb')
    elem.set('avail_capacity_kb')
    elem.set('used_capacity_kb')
    elem.set('device_type')
    elem.set('state')
    elem.set('journal_state')

    if detailed:
        pass

device_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class DeviceTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('device', selector='device')
        make_device(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=device_nsmap)

class DevicesTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('devices')
        elem = xmlutil.SubTemplateElement(root, 'device', selector='devices')
        make_device(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=device_nsmap)

class Controller(wsgi.Controller):
    """The Devices API controller for the OpenStack API."""
    _view_builder_class = devices_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        super(Controller, self).__init__()

    #def _get_zone_search_options(self):
    #    """Return zone search options allowed by non-admin."""
    #    return ('id', 'name', 'public_ip')

    @wsgi.serializers(xml=DevicesTemplate)
    def index(self, req):
        """Get device list."""
        context = req.environ['vsm.context']
        devices = self.conductor_api.device_get_all(context)
        LOG.info('vsm/api/v1/devices.py devices:%s' % devices)

        return self._view_builder.index(req, devices)

    @wsgi.serializers(xml=DevicesTemplate)
    def detail(self, req,search_opts=None):
        """Get device list."""
        context = req.environ['vsm.context']
        device_id = req.GET.get('device_id',None)
        devices=[]
        if device_id:
            devices =[(dict(db.device_get(context,device_id)))]
            LOG.info('get device %s:%s'%(device_id,devices))
        return self._view_builder.index(req, devices)

    def get_smart_info(self, req, search_opts=None):
        """Get device list."""
        context = req.environ['vsm.context']
        device_id = req.GET.get('device_id',None)
        device_path = req.GET.get('device_path',None)
        if device_id:
                body = {'server': db.init_node_get_by_device_id(context,device_id),
                        'device_path': device_path
                }
                device_data_dict = self.scheduler_api.get_smart_info(context, body)
                LOG.info('get smart device info = %s:%s'%(device_path,device_data_dict))
        return {'smart_info':device_data_dict}

    def get_available_disks(self,req,):
        context = req.environ['vsm.context']
        server_id = req.GET.get('server_id',None)
        body = {'server_id':server_id}
        disk_list = self.scheduler_api.get_available_disks(context, body)
        return {"available_disks":disk_list}
    #@wsgi.serializers(xml=ZonesTemplate)
    #def create(self, req, body):
    #    """create zone."""
    #    LOG.info("CEPH_LOG zone create body: %s" % body)
    #    return {"zone": {"id":1,"name":"2"}}
    #
    #@wsgi.serializers(xml=ZonesTemplate)
    #def show(self, req, id):
    #    """update zone."""
    #    LOG.info("CEPH_LOG zone show id: %s" % id)
    #    return {"zone": {"id":1,"name":"2"}}

    #@wsgi.serializers(xml=ZonesTemplate)
    #def update(self, req, id, body):
    #    """update zone."""
    #    LOG.info("CEPH_LOG zone update body: %s" % body)
    #    return {"zone": {"id":1,"name":"2"}}

    #def delete(self, req, id):
    #    """delete zone."""
    #    LOG.info("CEPH_LOG zone delete id: %s" % id)
    #    return webob.Response(status_int=202)

def create_resource(ext_mgr):
    return wsgi.Resource(Controller(ext_mgr))

#def remove_invalid_options(context, search_options, allowed_search_options):
#    """Remove search options that are not valid for non-admin API/context."""
#    if context.is_admin:
#        # Allow all options
#        return
#    # Otherwise, strip out all unknown options
#    unknown_options = [opt for opt in search_options
#                       if opt not in allowed_search_options]
#    bad_options = ", ".join(unknown_options)
#    log_msg = _("Removing options '%(bad_options)s' from query") % locals()
#    LOG.debug(log_msg)
#    for opt in unknown_options:
#        del search_options[opt]
