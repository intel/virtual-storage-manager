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
from vsm.api.views import servers as servers_views
from vsm.openstack.common import jsonutils
from vsm import utils
from vsm import conductor
from vsm import scheduler
from vsm.scheduler import rpcapi as scheduler_rpcapi

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_server(elem, detailed=False):
    elem.set('id')
    elem.set('host')
    elem.set('primary_public_ip')
    elem.set('secondary_public_ip')
    elem.set('cluster_ip')
    elem.set('raw_ip')
    #elem.set('zone')
    elem.set('zone_id')
    elem.set('osds')
    elem.set('type')
    elem.set('status')

    if detailed:
        pass

    #xmlutil.make_links(elem, 'links')

def _translate_server_summary_view(context, server):
    if not server:
        return {"id": "",
                "host": "",
                "primary_public_ip": "",
                "secondary_public_ip": "",
                "cluster_ip": "",
                "raw_ip":"",
                "ceph_ver":"",
                "zone_id": "",
                "osds": "",
                "type": "",
                "status": ""}
    d = {"id": server["id"],
        "host": server["host"],
        "primary_public_ip": server["primary_public_ip"],
        "secondary_public_ip": server["secondary_public_ip"],
        "cluster_ip": server["cluster_ip"],
        "raw_ip":"192.168.1.3,192.168.2.3,192.168.3.3",
        "zone_id": server["zone_id"],
        "ceph_ver":server["ceph_ver"],
        "osds": server['data_drives_number'],
        "type": server['type'],
        "status": server['status']}
    if d['type'] is None:
        d['type'] = ""
    return d

server_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class ServerTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('server', selector='server')
        make_server(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=server_nsmap)

class ServersTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('servers')
        elem = xmlutil.SubTemplateElement(root, 'server', selector='servers')
        make_server(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=server_nsmap)

class ServersController(wsgi.Controller):
    """The Servers API controller for the OpenStack API."""
    _view_builder_class = servers_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.scheduler_rpcapi = scheduler_rpcapi.SchedulerAPI()
        self.ext_mgr = ext_mgr
        super(ServersController, self).__init__()

    def _get_server_search_options(self):
        """Return server search options allowed by non-admin."""
        return ('id', 'name', 'public_ip')

    @wsgi.serializers(xml=ServersTemplate)
    def index(self, req):
        """Get server list."""
        #search_opts = {}
        #search_opts.update(req.GET)
        context = req.environ['vsm.context']
        #remove_invalid_options(context,
        #                        search_opts,
        #                        self._get_server_search_options)
        servers = self.conductor_api.get_server_list(context)
        #server_list = servers.values()
        #sorted_servers = sorted(server_list,
        #                      key=lambda item: item['id'])

        return self._view_builder.index(servers)

    @wsgi.serializers(xml=ServersTemplate)
    def update(self, req, id, body):
        """update server."""
        LOG.info("CEPH_LOG server update body: %s" % body)
        return {"server": {"id":1,"name":"2"}}

    @wsgi.serializers(xml=ServersTemplate)
    def show(self, req, id):
        """update cluster."""
        context = req.environ['vsm.context']
        server = self.conductor_api.get_server(context, id)
        LOG.info("CEPH_LOG cluster show id: %s" % id)
        return {"server": _translate_server_summary_view(context, server)}

    def add(self, req, body=None):
        LOG.info('CEPH_LOG add-server body %s ' % body)
        context = req.environ['vsm.context']

        self.scheduler_api.add_servers(context, body)
        return webob.Response(status_int=202)

    def remove(self, req, body=None):
        LOG.info('CEPH_LOG remove body %s ' % body)
        context = req.environ['vsm.context']

        self.scheduler_api.remove_servers(context, body)
        return webob.Response(status_int=202)

    def reset_status(self, req, body=None):
        LOG.debug('reset_status = %s' % body)
        context = req.environ['vsm.context']
        init_node_id = body.get('servers', None)
        if not init_node_id:
            return webob.Response(status_int=202)

        node_ref = self.conductor_api.init_node_get_by_id(context,
            init_node_id)
        if node_ref:
            if node_ref['status'] == 'available':
                return webob.Response(status_int=202)
            if node_ref['status'].lower().find('error') != -1:
                return webob.Response(status_int=202)

        else:
            return webob.Response(status_int=202)

        self.conductor_api.init_node_update_status_by_id(context,
            init_node_id, 'Active')

        return {'status': 'ok'}
        return webob.Response(status_int=202)

    def start(self, req, body=None):
        LOG.info('DEBUG start-server body %s ' % body)
        context = req.environ['vsm.context']

        self.scheduler_rpcapi.start_server(context, body)
        return webob.Response(status_int=202)

    def stop(self, req, body=None):
        LOG.info('DEBUG stop-server body %s ' % body)
        context = req.environ['vsm.context']

        self.scheduler_rpcapi.stop_server(context, body)
        return webob.Response(status_int=202)

    def ceph_upgrade(self, req, body=None):
        LOG.info('DEBUG ceph_upgrade body %s ' % body)
        context = req.environ['vsm.context']
        ret = self.scheduler_rpcapi.ceph_upgrade(context, body)
        LOG.info('DEBUG ceph_upgrade ret %s ' % ret)
        return ret
        #return webob.Response(status_int=202)

def create_resource(ext_mgr):
    return wsgi.Resource(ServersController(ext_mgr))

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
