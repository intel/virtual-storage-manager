# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
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

import webob
import commands
from webob import exc
from vsm.api import extensions
from vsm.api.openstack import wsgi
from vsm.agent import storagepoolusage
from vsm.agent import appnodes
from vsm.api import xmlutil
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.api.views import poolusages as poolusages_views
from vsm.openstack.common.gettextutils import _
from vsm.scheduler.api import API as scheduler_api

"""Storage pool usage API"""

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_poolusage(elem, detailed=False):
    elem.set('id')
    elem.set('vsmapp_id')
    elem.set('pool_id')
    elem.set('attach_status')
    elem.set('attach_at')

    if detailed:
        pass

poolusage_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class PoolUsageTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('poolusage', selector='poolusage')
        make_poolusage(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=poolusage_nsmap)

class PoolUsagesTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('poolusages')
        elem = xmlutil.SubTemplateElement(root, 'poolusage', selector='poolusages')
        make_poolusage(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=poolusage_nsmap)

class PoolUsagesController(wsgi.Controller):
    """The storage pool usage API controller."""
    _view_builder_class = poolusages_views.ViewBuilder

    def __init__(self):
        self.scheduler_api = scheduler_api()
        super(PoolUsagesController, self).__init__()

    @wsgi.serializers(xml=PoolUsagesTemplate)
    def index(self, req):
        """Returns a summary list of pool usages."""
        return self._get_usages(req)

    def _get_usages(self, req):
        """Returns a list of pool usages, transformed through view builder."""
        context = req.environ['vsm.context']
        usages = storagepoolusage.get_all(context)
        usage_view = self._view_builder.index(usages)
        return usage_view

    @wsgi.response(202)
    def create(self, req, body):
        LOG.debug(_('Creating new pool usages %s'), body)
        LOG.info(' Creating new pool usages')

        context = req.environ['vsm.context']
        pools = body['poolusages']
        cinder_volume_host_list = pools.values()

        # check openstack access
        nodes = appnodes.get_all_nodes(context)
        auth_host = nodes[0].get("os_auth_url").split(":")[1][2:]
        for host in cinder_volume_host_list:
            (status, output) = commands.getstatusoutput('ssh %s "crudini --version"' % host)
            LOG.info(str(status) + "========" + output)
            if "command not found" in output:
                return {'status': 'bad', 'host': host}
        id_list = body['poolusages']
        info = storagepoolusage.create(context, id_list)
        LOG.info(' pools_info = %s' % info)
        self.scheduler_api.present_storage_pools(context, info)
        return {'status': 'ok'}

    @wsgi.serializers(xml=PoolUsagesTemplate)
    def update(self, req, id, body):
        LOG.debug(_('Updating pool usage by vsmapp id %s' % id))
        context = req.environ['vsm.context']

        if not self.is_valid_body(body, 'poolusages'):
            raise exc.HTTPBadRequest()

        body = body.get('poolusages')
        LOG.debug('PUT body: %s' % body)

        if id is None:
            expl = _('Request body and URI mismatch: No vsmapp_id')
            raise webob.exc.HTTPBadRequest(explanation=expl)
        # convert from unicode to str
        id = str(id)
        status = body.get('attach_status', None)
        terminate = body.get('is_terminate', None)

        if not status and not terminate:
            expl = _('Request body and URI mismatch: attach_status or is_terminate required.')
            raise webob.exc.HTTPBadRequest(explanation=expl)

        storagepoolusage.update(context, id, status, terminate)
        return webob.Response(status_int=201)

    @wsgi.serializers(xml=PoolUsagesTemplate)
    def delete(self, req, id):
        """delete pool usage by id."""
        LOG.debug(_('Removing pool ussage by id %s' % id))
        context = req.environ['vsm.context']
        if id is None:
            expl = _('Request body and URI mismatch')
            raise webob.exc.HTTPBadRequest(explanation=expl)
        id = str(id)
        storagepoolusage.destroy(context, id)
        return webob.Response(status_int=201)

class Poolusages(extensions.ExtensionDescriptor):
    """storage pool usage extension."""

    name = 'Poolusages'
    alias = 'poolusages'
    namespace = 'http://docs.openstack.org/storage/ext/poolusages/api/v1'
    updated = '2014-03-19T00:00:00+00:00'

    def get_resources(self):
        resources = []
        res = extensions.ResourceExtension(Poolusages.alias, PoolUsagesController())
        resources.append(res)
        return resources
