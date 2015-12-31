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
from vsm.api.views import osds as osds_views
from vsm.api.views import summary as summary_view
from vsm import conductor
from vsm import scheduler
from vsm import exception
from vsm import db

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_osd(elem, detailed=False):
    elem.set('id')
    elem.set('osd_name')
    elem.set('state')
    elem.set('operation_status')
    elem.set('weight')
    elem.set('device_id')
    elem.set('service_id')

    if detailed:
        pass

osd_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class OSDTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('osd', selector='osd')
        make_osd(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=osd_nsmap)

class OSDsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('osds')
        elem = xmlutil.SubTemplateElement(root, 'osd', selector='osds')
        make_osd(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=osd_nsmap)

class Controller(wsgi.Controller):
    """The OSDs API controller for the OpenStack API."""
    _view_builder_class = osds_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        super(Controller, self).__init__()

    #def _get_zone_search_options(self):
    #    """Return zone search options allowed by non-admin."""
    #    return ('id', 'name', 'public_ip')

    def _get_osd(self, context, req, id):
        """Utility function for looking up an instance by id."""
        try:
            osd = self.conductor_api.osd_get(context, id)
        except exception.NotFound:
            msg = _("OSD could not be found")
            raise exc.HTTPNotFound(explanation=msg)
        return osd

    @wsgi.serializers(xml=OSDsTemplate)
    def show(self, req, id):
        """Return data about the given osd."""
        context = req.environ['vsm.context']

        try:
            osd = self._get_osd(context, req, id)
            error = self.conductor_api.ceph_error(context)
            LOG.info('JIYOU show')
            if error:
                osd['state'] = error
                osd['operation_status'] = error
                osd['device']['state'] = error
                osd['device']['journal_state'] = error
                osd['device']['osd_state'] = error
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return {'osd': osd}

    @wsgi.serializers(xml=OSDsTemplate)
    def index(self, req):
        """Get osd list."""
        context = req.environ['vsm.context']
        error = self.conductor_api.ceph_error(context)
        osds = self.conductor_api.osd_state_get_all(context)
        if error:
            for osd in osds:
                osd['state'] = error
                osd['operation_status'] = error
                osd['device']['state'] = error
                osd['device']['journal_state'] = error
                osd['device']['osd_state'] = error

        LOG.info('vsm/api/v1/osds.py osds:%s' % osds)

        return self._view_builder.index(req, osds)

    @wsgi.serializers(xml=OSDsTemplate)
    def detail(self, req):

        """Get osd list."""
        context = req.environ['vsm.context']
        service_id = req.GET.get('service_id', None)
        error = self.conductor_api.ceph_error(context)
        LOG.info('vsm/api/v1/osds.py detailed service_id:%s' % service_id)
        if service_id:
            osds = db.osd_get_by_service_id(context, service_id)
            if len(osds) > 0:
                LOG.info('device=%s'%osds[0].device)
        else:
            limit = req.GET.get('limit', None)
            marker = req.GET.get('marker', None)
            sort_keys = req.GET.get('sort_keys', None)
            sort_dir = req.GET.get('sort_dir', None)
            osds = self.conductor_api.osd_state_get_all(context, limit,
                                                        marker, sort_keys,
                                                        sort_dir)
        if error:
            for osd in osds:
                osd['state'] = error
                osd['operation_status'] = error
                osd['device']['state'] = error
                osd['device']['journal_state'] = error
                osd['device']['osd_state'] = error

        LOG.info('vsm/api/v1/osds.py detailed osds:%s' % osds)

        return self._view_builder.detail(req, osds)
    @wsgi.serializers(xml=OSDsTemplate)
    def detail_filter_and_sort(self, req):

        """Get osd list."""
        context = req.environ['vsm.context']
        limit = req.GET.get('limit', None)
        marker = req.GET.get('marker', None)
        sort_keys = req.GET.get('sort_keys', None)
        sort_dir = req.GET.get('sort_dir', None)
        search_opts = {
            'osd_name':req.GET.get('osd_name', ''),
            'server_name':req.GET.get('server_name', ''),
            'zone_name':req.GET.get('zone_name', ''),
            'state':req.GET.get('state', ''),
        }
        error = self.conductor_api.ceph_error(context)
        osds = self.conductor_api.osd_state_get_all(context, limit,
                                                    marker, sort_keys,
                                                    sort_dir,search_opts)

        if error:
            for osd in osds:
                osd['state'] = error
                osd['operation_status'] = error
                osd['device']['state'] = error
                osd['device']['journal_state'] = error
                osd['device']['osd_state'] = error

        LOG.info('vsm/api/v1/osds.py detail_filter_and_sort osds:%s' % osds)

        return self._view_builder.detail(req, osds)


    def refresh(self, req):
        """
        :param req:
        :return:
        refresh osd status
        """
        context = req.environ['vsm.context']
        self.scheduler_api.osd_refresh(context)

    #TODO scheduler exe
    @wsgi.response(204)
    def delete(self, req, id):
        """delete a osd."""
        LOG.info("osd_delete")
        context = req.environ['vsm.context']
        osd = self._get_osd(context, req, id)
        self.conductor_api.osd_delete(context, osd['id'])

    @wsgi.response(202)
    @wsgi.serializers(xml=OSDsTemplate)
    @wsgi.action('remove')
    def _action_remove(self, req, id, body):
        context = req.environ['vsm.context']
        LOG.info("action_remove")
        self.scheduler_api.osd_remove(context, id)
        return webob.Response(status_int=202)

    @wsgi.response(202)
    @wsgi.serializers(xml=OSDsTemplate)
    @wsgi.action('restart')
    def _action_restart(self, req, id, body):
        context = req.environ['vsm.context']
        LOG.info("action_restart")
        self.scheduler_api.osd_restart(context, id)
        return webob.Response(status_int=202)

    @wsgi.response(202)
    @wsgi.serializers(xml=OSDsTemplate)
    @wsgi.action('restore')
    def _action_restore(self, req, id, body):
        context = req.environ['vsm.context']
        LOG.info("osd_restore osd_id = %s" % id)
        self.scheduler_api.osd_restore(context, id)
        return webob.Response(status_int=202)

    @wsgi.response(202)
    @wsgi.serializers(xml=OSDsTemplate)
    @wsgi.action('add')
    def _action_add(self, req, id, body):
        context = req.environ['vsm.context']
        LOG.info("osd_add osd_id = %s" % id)
        self.scheduler_api.osd_add(context, id)
        return webob.Response(status_int=202)

    def add_new_disks_to_cluster(self, req, body):
        context = req.environ['vsm.context']
        LOG.info("osd_add body= %s" % body)
        self.scheduler_api.add_new_disks_to_cluster(context, body)
        return webob.Response(status_int=202)

    def add_batch_new_disks_to_cluster(self, req, body):
        context = req.environ['vsm.context']
        LOG.info("batch_osd_add body= %s" % body)
        ret = self.scheduler_api.add_batch_new_disks_to_cluster(context, body)
        LOG.info("batch_osd_add ret= %s" % ret)
        return ret

    def summary(self, req, cluster_id = None):
        #LOG.info('osd-summary body %s ' % body)
        context = req.environ['vsm.context']
        if cluster_id:
            sum = db.summary_get_by_cluster_id_and_type(context, cluster_id, 'osd')
        else:
            sum = db.summary_get_by_type_first(context, 'osd')
        #sum = db.summary_get_by_cluster_id_and_type(context, 1, 'osd')

        vb = summary_view.ViewBuilder()
        return vb.basic(sum, 'osd')

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
