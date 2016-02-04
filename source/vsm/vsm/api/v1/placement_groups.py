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
from vsm.api.openstack import wsgi
from vsm.api import xmlutil
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.api.views import placement_groups as placement_group_views
from vsm.api.views import summary as summary_view
from vsm import conductor
from vsm import scheduler
from vsm import exception
from vsm import db
LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_placement_group(elem, detailed=False):
    elem.set('id')
    elem.set('name')
    elem.set('address')
    elem.set('health')
    elem.set('detail')
    elem.set('skew')
    elem.set('latency')
    elem.set('kb_total')
    elem.set('kb_used')
    elem.set('kb_avail')
    elem.set('percent_avail')

    if detailed:
        pass

placement_group_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class PlacementGroupTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('placement_group', selector='placement_group')
        make_placement_group(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=placement_group_nsmap)

class PlacementGroupsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('placement_groups')
        elem = xmlutil.SubTemplateElement(root, 'placement_group', selector='placement_groupss')
        make_placement_group(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=placement_group_nsmap)

class Controller(wsgi.Controller):
    """The placement_groups API controller for the OpenStack API."""
    _view_builder_class = placement_group_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        super(Controller, self).__init__()

    #def _get_zone_search_options(self):
    #    """Return zone search options allowed by non-admin."""
    #    return ('id', 'name', 'public_ip')

    def _get_placement_group(self, context, req, id):
        """Utility function for looking up an instance by id."""
        try:
            placement_group = self.conductor_api.pg_get(context, id)
        except exception.NotFound:
            msg = _("placement_group could not be found")
            raise exc.HTTPNotFound(explanation=msg)
        return placement_group

    @wsgi.serializers(xml=PlacementGroupsTemplate)
    def show(self, req, id):
        """Return data about the given placement_group."""
        context = req.environ['vsm.context']

        try:
            placement_group = self._get_placement_group(context, req, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return {'placement_group': placement_group}

    @wsgi.serializers(xml=PlacementGroupsTemplate)
    def index(self, req):
        """Get placement_group list."""
        #search_opts = {}
        #search_opts.update(req.GET)
        context = req.environ['vsm.context']
        #remove_invalid_options(context,
        #                        search_opts,
        #                        self._get_zone_search_options)
        #zones = self.conductor_api.get_zone_list(context)
        limit = req.GET.get('limit', None)
        marker = req.GET.get('marker', None)
        sort_keys = req.GET.get('sort_keys', None)
        sort_dir = req.GET.get('sort_dir', None)

        placement_groups = self.conductor_api.pg_get_all(context, limit,
                                                         marker, sort_keys,
                                                         sort_dir)
        LOG.info('vsm/api/v1/placement_group.py placement_groups:%s' % placement_groups)

        return self._view_builder.index(req, placement_groups)

    @wsgi.serializers(xml=PlacementGroupsTemplate)
    def detail(self, req):

        """Get placement_group list."""
        #search_opts = {}
        #search_opts.update(req.GET)
        context = req.environ['vsm.context']
        #remove_invalid_options(context,
        #                        search_opts,
        #                        self._get_zone_search_options)
        #zones = self.conductor_api.get_zone_list(context)
        limit = req.GET.get('limit', None)
        marker = req.GET.get('marker', None)
        sort_keys = req.GET.get('sort_keys', None)
        sort_dir = req.GET.get('sort_dir', None)

        placement_groups = self.conductor_api.pg_get_all(context, limit,
                                                         marker, sort_keys,
                                                         sort_dir)
        #LOG.info('vsm/api/v1/placement_groups.py detailed placement_groups:%s' % placement_groups)

        return self._view_builder.detail(req, placement_groups)

    def summary(self, req, body = None,  cluster_id = None):
        LOG.info('CEPH_LOG placement_group-summary body %s ' % body)
        context = req.environ['vsm.context']
        if cluster_id:
            sum = db.summary_get_by_cluster_id_and_type(context, cluster_id, 'pg')
        else:
            sum = db.summary_get_by_type_first(context, 'pg')
        #sum = db.summary_get_by_cluster_id_and_type(context, 1, 'pg')
        vb = summary_view.ViewBuilder()
        return vb.basic(sum, 'placement_group')

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
