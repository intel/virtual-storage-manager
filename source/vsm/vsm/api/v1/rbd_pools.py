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
from vsm.api.views import rbd_pools as rbd_pool_views
from vsm import conductor
from vsm import scheduler
from vsm import exception

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_rbd_pool(elem, detailed=False):
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

rbd_pool_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class RBDPoolTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('rbd_pool', selector='rbd_pool')
        make_rbd_pool(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=rbd_pool_nsmap)

class RBDPoolsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('rbd_pools')
        elem = xmlutil.SubTemplateElement(root, 'rbd_pool', selector='rbd_poolss')
        make_rbd_pool(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=rbd_pool_nsmap)

class Controller(wsgi.Controller):
    """The rbd_pools API controller for the OpenStack API."""
    _view_builder_class = rbd_pool_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        super(Controller, self).__init__()

    #def _get_zone_search_options(self):
    #    """Return zone search options allowed by non-admin."""
    #    return ('id', 'name', 'public_ip')

    def _get_rbd_pool(self, context, req, id):
        """Utility function for looking up an instance by id."""
        try:
            rbd_pool = self.conductor_api.rbd_pool_get(context, id)
        except exception.NotFound:
            msg = _("rbd_pool could not be found")
            raise exc.HTTPNotFound(explanation=msg)
        return rbd_pool

    @wsgi.serializers(xml=RBDPoolsTemplate)
    def show(self, req, id):
        """Return data about the given rbd_pool."""
        context = req.environ['vsm.context']

        try:
            rbd_pool = self._get_rbd_pool(context, req, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return {'rbd_pool': rbd_pool}

    @wsgi.serializers(xml=RBDPoolsTemplate)
    def index(self, req):
        """Return a list of rbd pools."""

        context = req.environ['vsm.context']
        limit = req.GET.get('limit', None)
        marker = req.GET.get('marker', None)
        sort_keys = req.GET.get('sort_keys', None)
        sort_dir = req.GET.get('sort_dir', None)

        rbd_pools = self.conductor_api.rbd_get_all(context,
                                                   limit=limit,
                                                   marker=marker,
                                                   sort_keys=sort_keys,
                                                   sort_dir=sort_dir)
        LOG.info('vsm/api/v1/rbd_pool.py rbd_pools:%s' % rbd_pools)

        return self._view_builder.index(req, rbd_pools)

    @wsgi.serializers(xml=RBDPoolsTemplate)
    def detail(self, req):

        """Get rbd_pool list."""
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

        rbd_pools = self.conductor_api.rbd_get_all(context, limit, marker,
						   sort_keys, sort_dir)
        #LOG.info('vsm/api/v1/rbd_pools.py detailed rbd_pools:%s' % rbd_pools)

        return self._view_builder.detail(req, rbd_pools)

    def summary(self, req, body=None):
        LOG.info('CEPH_LOG rbd_pool-summary body %s ' % body)
        context = req.environ['vsm.context']
        return {'rbd-summary':{'epoch': 123,
                               'num_rbd_pools': 12,
                               'num_up_rbd_pools': 8,
                               'num_in_rbd_pools': 8,
                               'nearfull': False,
                               'full': False,
                               }}

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
