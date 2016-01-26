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
from vsm.api.views import mdses as mds_views
from vsm.api.views import summary as summary_view
from vsm import conductor
from vsm import scheduler
from vsm import exception

from vsm import db
LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_mds(elem, detailed=False):
    elem.set('id')
    elem.set('mds_name')
    elem.set('gid')
    elem.set('state')
    elem.set('address')

    if detailed:
        pass

mds_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class OSDTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('mds', selector='mds')
        make_mds(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=mds_nsmap)

class OSDsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('mdses')
        elem = xmlutil.SubTemplateElement(root, 'mds', selector='mdsess')
        make_mds(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=mds_nsmap)

class Controller(wsgi.Controller):
    """The OSDs API controller for the OpenStack API."""
    _view_builder_class = mds_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        super(Controller, self).__init__()

    #def _get_zone_search_options(self):
    #    """Return zone search options allowed by non-admin."""
    #    return ('id', 'name', 'public_ip')

    def _get_mds(self, context, req, id):
        """Utility function for looking up an instance by id."""
        try:
            mds = self.conductor_api.mds_get(context, id)
        except exception.NotFound:
            msg = _("MDS could not be found")
            raise exc.HTTPNotFound(explanation=msg)
        return mds

    @wsgi.serializers(xml=OSDsTemplate)
    def show(self, req, id):
        """Return data about the given mds."""
        context = req.environ['vsm.context']

        try:
            mds = self._get_mds(context, req, id)
            error = self.conductor_api.ceph_error(context)
            if error:
                mds['state'] = error
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return {'mds': mds}

    @wsgi.serializers(xml=OSDsTemplate)
    def index(self, req):
        """Get mds list."""
        #search_opts = {}
        #search_opts.update(req.GET)
        context = req.environ['vsm.context']
        #remove_invalid_options(context,
        #                        search_opts,
        #                        self._get_zone_search_options)
        #zones = self.conductor_api.get_zone_list(context)
        error = self.conductor_api.ceph_error(context)
        mdses = self.conductor_api.mds_get_all(context)
        if error:
            for mds in mdses:
                mds['state'] = error

        LOG.info('vsm/api/v1/mds.py mdss:%s' % mdses)

        return self._view_builder.index(req, mdses)

    @wsgi.serializers(xml=OSDsTemplate)
    def detail(self, req):

        """Get mds list."""
        #search_opts = {}
        #search_opts.update(req.GET)
        context = req.environ['vsm.context']
        #remove_invalid_options(context,
        #                        search_opts,
        #                        self._get_zone_search_options)
        #zones = self.conductor_api.get_zone_list(context)
        mdses = self.conductor_api.mds_get_all(context)
        LOG.info('vsm/api/v1/mdses.py detailed mdses:%s' % mdses)

        return self._view_builder.detail(req, mdses)

    #TODO scheduler exe
    @wsgi.response(204)
    def delete(self, req, id):
        """delete a mds."""
        LOG.info("mds_delete")
        context = req.environ['vsm.context']
        mds = self._get_mds(context, req, id)
        self.conductor_api.mds_delete(context, mds['id'])

    @wsgi.response(202)
    @wsgi.serializers(xml=OSDsTemplate)
    @wsgi.action('remove')
    def _action_remove(self, req, id, body):
        context = req.environ['vsm.context']
        mds = self._get_mds(context, req, id)

        LOG.info("action_remove")
        mds = self._get_mds(context, req, id)
        #self.conductor_api.mds_remove(context, mds['id'])
        self.scheduler_api.mds_remove(context, mds)
        return webob.Response(status_int=202)

    @wsgi.response(202)
    @wsgi.serializers(xml=OSDsTemplate)
    @wsgi.action('restart')
    def _action_restart(self, req, id, body):
        context = req.environ['vsm.context']
        mds = self._get_mds(context, req, id)

        LOG.info("action_restart")
        self.scheduler_api.mds_restart(context, mds)
        return webob.Response(status_int=202)

    @wsgi.response(202)
    @wsgi.serializers(xml=OSDsTemplate)
    @wsgi.action('restore')
    def _action_restore(self, req, id, body):
        context = req.environ['vsm.context']
        mds = self._get_mds(context, req, id)

        LOG.info("action_restore")
        mds['operation_status'] = FLAGS.vsm_status_present
        self.conductor_api.\
             mds_state_update_or_create(context, \
             mds, create=False)
        self.scheduler_api.mds_restore(context, mds)
        return webob.Response(status_int=202)

    def summary(self, req, body=None,cluster_id=None):
        LOG.info('CEPH_LOG mds-summary body %s ' % body)
        context = req.environ['vsm.context']
        if cluster_id:
            mds = db.summary_get_by_cluster_id_and_type(context, cluster_id, 'mds')
        else:
            mds = db.summary_get_by_type_first(context, 'mds')
        vb = summary_view.ViewBuilder()
        return vb.basic(mds, 'mds')

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
