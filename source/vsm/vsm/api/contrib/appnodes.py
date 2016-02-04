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
from webob import exc
from vsm import utils
from vsm.api import extensions
from vsm.api.openstack import wsgi
from vsm.agent import appnodes
from vsm.api import xmlutil
from vsm import flags
from vsm import conductor
from vsm import exception
from vsm.openstack.common import log as logging
from vsm.api.views import appnodes as appnodes_views
from vsm.openstack.common.gettextutils import _

"""App nodes API"""

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_appnode(elem, detailed=False):
    elem.set('id')
    elem.set('vsmapp_id')
    elem.set('ip')
    elem.set('ssh_status')
    elem.set('log_info')

    if detailed:
        elem.set('created_at')

vsmapp_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class AppnodeTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('appnode', selector='appnode')
        make_appnode(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=vsmapp_nsmap)

class AppnodesTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('appnodes')
        elem = xmlutil.SubTemplateElement(root, 'appnode', selector='appnodes')
        make_appnode(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=vsmapp_nsmap)

class AppnodesController(wsgi.Controller):
    """The vsm app nodes API controller."""
    _view_builder_class = appnodes_views.ViewBuilder

    def __init__(self):
        self.conductor_api = conductor.API()
        super(AppnodesController, self).__init__()

    @wsgi.serializers(xml=AppnodeTemplate)
    def show(self, req, id):
        """Get details info of an appnode."""
        context = req.environ['vsm.context']
        try:
            appnode = self.conductor_api.get_appnode(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        return {"appnode": appnode}

    @wsgi.serializers(xml=AppnodesTemplate)
    def index(self, req):
        """Returns a summary list of appnodes."""
        return self._get_nodes(req)

    def _get_nodes(self, req):
        """Returns a list of appnodes, transformed through view builder."""
        context = req.environ['vsm.context']
        nodes = appnodes.get_all_nodes(context)
        node_view = self._view_builder.index(nodes)
        return node_view

    def _get_appnodes_search_options(self):
        """Return appnodes search options allowed by non-admin."""
        return ('vsmapp_id',)

    @wsgi.response(202)
    def create(self, req, body):
        """create app nodes."""
        LOG.debug(_('Creating new app nodes %s'), body)

        if not self.is_valid_body(body, 'appnodes'):
            raise exc.HTTPBadRequest()

        context = req.environ['vsm.context']
        auth_openstack = body['appnodes']
        # if not isinstance(ip_list, list):
        #     expl = _('Invalid Request body: should be a list of IP address.')
        #     raise webob.exc.HTTPBadRequest(explanation=expl)
        node_list = appnodes.create(context, auth_openstack)
        node_view = self._view_builder.index(node_list)
        # for node in node_list:
            #LOG.info('Node %s, Node id: %s, Node ip: %s' % (node, node.id, node.ip))
            #ssh = utils.SSHClient(ip='10.239.131.170', user='root', key_file=r'~/.ssh/id_rsa')
            #ssh = utils.SSHClient(node.ip, 'root', '~/.ssh/id_rsa')
            #ret = ssh.check_ssh(retries=1)
            #status = 'reachable' if ret else 'unreachable'
            # status = 'reachable'
            # appnodes.update(context, node.id, status)

        return webob.Response(status_int=201)

    @wsgi.serializers(xml=AppnodesTemplate)
    def delete(self, req, id):
        """delete app node by id."""
        LOG.debug(_('Removing app node by id %s' % id))
        context = req.environ['vsm.context']
        if id is None:
            expl = _('Request body and URI mismatch')
            raise webob.exc.HTTPBadRequest(explanation=expl)
        id = str(id)
        appnodes.destroy(context, id)
        return webob.Response(status_int=201)

    @wsgi.serializers(xml=AppnodesTemplate)
    def update(self, req, id, body):
        LOG.debug(_('Updating app node by id %s' % id))
        context = req.environ['vsm.context']

        if not self.is_valid_body(body, 'appnode'):
            raise exc.HTTPBadRequest()

        body = body.get('appnode')
        LOG.debug('PUT body: %s' % body)

        if id is None:
            expl = _('Request body and URI mismatch: No appnode_id')
            raise webob.exc.HTTPBadRequest(explanation=expl)
        # convert from unicode to str
        id = str(id)
        os_tenant_name = body.get('os_tenant_name', None)
        os_username = body.get('os_username', None)
        os_password = body.get('os_password', None)
        os_auth_url = body.get('os_auth_url', None)

        if not os_tenant_name or not os_username or not os_password or not os_auth_url:
            expl = _('Request body and URI mismatch: os_tenant_name or os_username or os_password or os_auth_url required.')
            raise webob.exc.HTTPBadRequest(explanation=expl)

        appnodes.update(context, id, body)
        return webob.Response(status_int=201)

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

class Appnodes(extensions.ExtensionDescriptor):
    """Appnodes support."""

    name = 'Appnodes'
    alias = 'appnodes'
    namespace = 'http://docs.openstack.org/storage/ext/appnodes/api/v1'
    updated = '2014-03-12T00:00:00+00:00'

    def get_resources(self):
        resources = []
        res = extensions.ResourceExtension(Appnodes.alias, AppnodesController())

        resources.append(res)
        return resources
