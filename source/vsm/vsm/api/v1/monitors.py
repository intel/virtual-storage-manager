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
from vsm.api.views import monitors as mon_views
from vsm.api.views import summary as sum_views
from vsm import conductor
from vsm import scheduler
from vsm import db
from vsm import exception

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_monitor(elem, detailed=False):
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

mon = make_monitor

mon_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class MonitorTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('mon', selector='mon')
        make_monitor(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=mon_nsmap)

class MonitorsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('mons')
        elem = xmlutil.SubTemplateElement(root, 'mon', selector='mons')
        make_monitor(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=mon_nsmap)

class Controller(wsgi.Controller):
    """The Monitor API controller for the OpenStack API."""
    _view_builder_class = mon_views.ViewBuilder

    def __init__(self, ext_mgr):
        super(Controller, self).__init__()
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()

    @wsgi.serializers(xml=MonitorsTemplate)
    def show(self, req, id):
        """Return data about the given mon."""
        context = req.environ['vsm.context']

        try:
            mon = db.monitor_get(context, id)
            error = self.conductor_api.ceph_error(context)
            if error:
                mon['health'] = error

        except exception.NotFound:
            raise exc.HTTPNotFound()

        return self._view_builder.show(mon)

    @wsgi.serializers(xml=MonitorsTemplate)
    def index(self, req):
        """Get mon list."""
        #search_opts = {}
        #search_opts.update(req.GET)
        context = req.environ['vsm.context']

        mons = db.monitor_get_all(context)
        error = self.conductor_api.ceph_error(context)
        if error:
            for mon in mons:
                mons['health'] = error

        LOG.info('vsm/api/v1/mon.py mons:%s' % mons)

        return self._view_builder.index(mons)

    @wsgi.serializers(xml=MonitorsTemplate)
    def detail(self, req):

        """Get mon list."""
        #search_opts = {}
        #search_opts.update(req.GET)
        context = req.environ['vsm.context']
        #remove_invalid_options(context,
        #                        search_opts,
        #                        self._get_zone_search_options)
        #zones = self.conductor_api.get_zone_list(context)
        mons = db.monitor_get_all(context)
        LOG.info('vsm/api/v1/mons.py detailed mons:%s' % mons)

        return self._view_builder.detail(mons)

    @wsgi.response(202)
    def delete(self, req, id):
        """delete a mon in db."""
        context = req.environ['vsm.context']
        mon = db.monitor_get(context, id)

        db.monitor_destroy(context, mon.get('name'))

    @wsgi.response(202)
    @wsgi.action('restart')
    def _action_restart(self, req, id, body):
        context = req.environ['vsm.context']
        LOG.info("action_restart")
        self.scheduler_api.monitor_restart(context, id)
        return webob.Response(status_int=202)

    def summary(self, req, cluster_id=None):
        LOG.info('mon-summary.')
        context = req.environ['vsm.context']
        if cluster_id:
            sum = db.summary_get_by_cluster_id_and_type(context, cluster_id, 'mon')
        else:
            sum = db.summary_get_by_type_first(context, 'mon')
        #sum = db.summary_get_by_cluster_id_and_type(context, 1, 'mon')
        return sum_views.ViewBuilder().basic(sum, 'monitor')

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
