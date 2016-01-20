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

import webob
from webob import exc
import re

from vsm.api import common
from vsm.api.openstack import wsgi
from vsm.api import xmlutil
from vsm import exception
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.api.views import zones as zones_views
from vsm.openstack.common import jsonutils
from vsm import utils
from vsm import conductor
from vsm.conductor import rpcapi as conductor_rpcapi
from vsm import scheduler
from vsm import db

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_zone(elem, detailed=False):
    elem.set('id')
    elem.set('name')

    if detailed:
        pass

    #xmlutil.make_links(elem, 'links')

zone_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class ZoneTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('zone', selector='zone')
        make_zone(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=zone_nsmap)

class ZonesTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('zones')
        elem = xmlutil.SubTemplateElement(root, 'zone', selector='zones')
        make_zone(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=zone_nsmap)

class ZonesController(wsgi.Controller):
    """The Servers API controller for the OpenStack API."""
    _view_builder_class = zones_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        super(ZonesController, self).__init__()

    def _get_zone_search_options(self):
        """Return zone search options allowed by non-admin."""
        return ('id', 'name', 'public_ip')

    @wsgi.serializers(xml=ZonesTemplate)
    def index(self, req):
        """Get zone list."""
        search_opts = {}
        search_opts.update(req.GET)
        context = req.environ['vsm.context']
        remove_invalid_options(context,
                                search_opts,
                                self._get_zone_search_options)
        zones = self.conductor_api.get_zone_list(context)

        #zone_list = zones.values()
        #sorted_zones = sorted(zone_list,
        #                      key=lambda item: item['id'])
        #LOG.info('vsm/api/v1/zones.py severs')

        return self._view_builder.index(zones)

    @wsgi.serializers(xml=ZonesTemplate)
    def create(self, req, body):
        """create zone."""
        #LOG.info("CEPH_LOG zone create body: %s" % body)
        context = req.environ['vsm.context']
        self.scheduler_api.add_new_zone(context, body)
        return webob.Response(status_int=202)

    @wsgi.serializers(xml=ZonesTemplate)
    def show(self, req, id):
        """update zone."""
        LOG.info("CEPH_LOG zone show id: %s" % id)
        return {"zone": {"id":1,"name":"2"}}

    @wsgi.serializers(xml=ZonesTemplate)
    def update(self, req, id, body):
        """update zone."""
        LOG.info("CEPH_LOG zone update body: %s" % body)
        return {"zone": {"id":1,"name":"2"}}

    def delete(self, req, id):
        """delete zone."""
        LOG.info("CEPH_LOG zone delete id: %s" % id)
        return webob.Response(status_int=202)

    def osd_locations_choices(self,req):
        context = req.environ['vsm.context']
        osd_locations = db.osd_locations_choices_by_type(context,type=1)
        LOG.info("CEPH_LOG zone osd_locations_choices:%s"%osd_locations)
        return {'osd_locations_choices':osd_locations}

    def get_zone_not_in_crush_list(self,req):
        context = req.environ['vsm.context']
        zone_not_in_crush = db.zone_get_all_not_in_crush(context)
        LOG.info("CEPH_LOG zone get_zone_not_in_crush_list:%s"%zone_not_in_crush)
        return {'zone_not_in_crush':zone_not_in_crush}

    def add_zone_to_crushmap_and_db(self,req,body):
        context = req.environ['vsm.context']
        self.scheduler_api.add_zone_to_crushmap_and_db(context,body)
        return body

def create_resource(ext_mgr):
    return wsgi.Resource(ZonesController(ext_mgr))

def remove_invalid_options(context, search_options, allowed_search_options):
    """Remove search options that are not valid for non-admin API/context."""
    if context.is_admin:
        # Allow all options
        return
    # Otherwise, strip out all unknown options
    unknown_options = [opt for opt in search_options
                       if opt not in allowed_search_options]
    bad_options = ", ".join(unknown_options)
    log_msg = _("Removing options '%(bad_options)s' from query") % locals()
    LOG.debug(log_msg)
    for opt in unknown_options:
        del search_options[opt]
