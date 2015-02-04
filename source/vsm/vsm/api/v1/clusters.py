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
import json
from vsm.api import common
from vsm.api.openstack import wsgi
from vsm.api import xmlutil
from vsm import exception
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.api.views import clusters as clusters_views
from vsm.api.views import summary as summary_view
from vsm.openstack.common import jsonutils
from vsm import utils
from vsm import conductor
from vsm import scheduler
from vsm import db

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_cluster(elem, detailed=False):
    elem.set('id')
    elem.set('name')
    elem.set('file_system')
    elem.set('journal_size')
    elem.set('size')
    elem.set('primary_public_network')
    elem.set('secondary_public_network')
    elem.set('cluster_network')
    elem.set('primary_public_ip_netmask')
    elem.set('secondary_public_ip_netmask')
    elem.set('cluster_ip_netmask')

    if detailed:
        pass

    #xmlutil.make_links(elem, 'links')

cluster_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class ClusterTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('cluster', selector='cluster')
        make_cluster(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=cluster_nsmap)

class ClustersTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('clusters')
        elem = xmlutil.SubTemplateElement(root, 'cluster', selector='clusters')
        make_cluster(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=cluster_nsmap)

class ClusterController(wsgi.Controller):
    """The Cluster API controller for the OpenStack API."""
    _view_builder_class = clusters_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        super(ClusterController, self).__init__()

    def _get_server_search_options(self):
        """Return server search options allowed by non-admin."""
        return ('id', 'name', 'public_ip')

    @wsgi.serializers(xml=ClustersTemplate)
    def index(self, req):
        """Get cluster list."""
        search_opts = {}
        search_opts.update(req.GET)
        context = req.environ['vsm.context']
        remove_invalid_options(context,
                                search_opts,
                                self._get_server_search_options)
        clusters = self.conductor_api.get_cluster_list(context)
        #server_list = servers.values()
        #sorted_servers = sorted(server_list,
        #                      key=lambda item: item['id'])

        return self._view_builder.index(clusters)

    #@wsgi.serializers(xml=ClustersTemplate)
    def create(self, req, body):
        """create cluster."""
        LOG.info("CEPH_LOG cluster create body: %s" % body)
        context = req.environ['vsm.context']
        server_list = body['cluster']['servers']
        LOG.info('Begin to call scheduler.createcluster')
        self.scheduler_api.create_cluster(context, server_list)
        return webob.Response(status_int=202)

    def intergrate(self, req,body):
        """
        intergrate an existing ceph cluster
        """
        LOG.info("CEPH_LOG cluster intergrate body" )
        context = req.environ['vsm.context']
        #server_list = body['cluster']['servers']
        LOG.info('Begin to call scheduler.intergrate_cluster')
        self.scheduler_api.intergrate_cluster(context)

    @wsgi.serializers(xml=ClustersTemplate)
    def show(self, req, id):
        """update cluster."""
        LOG.info("CEPH_LOG cluster show id: %s" % id)
        return {"cluster": {"id":1,"name":"2"}}

    @wsgi.serializers(xml=ClustersTemplate)
    def update(self, req, id, body):
        """update cluster."""
        LOG.info("CEPH_LOG cluster update body: %s" % body)
        return {"cluster": {"id":1,"name":"2"}}

    def delete(self, req, id):
        """delete cluster."""
        LOG.info("CEPH_LOG cluster delete id: %s" % id)
        return webob.Response(status_int=202)

    def summary(self, req):
        #LOG.info('osd-summary body %s ' % body)
        context = req.environ['vsm.context']
        #TODO: as we have only one cluster for now, the cluster_id
        #has been hardcoded. In furture, client should pass
        # the cluster id by url.
        sum = db.summary_get_by_cluster_id_and_type(context, 1, 'cluster')
        vb = summary_view.ViewBuilder()
        return vb.basic(sum, 'cluster')

    def refresh(self, req):
        """
        :param req:
        :return:
        refresh cluster status
        """
        context = req.environ['vsm.context']
        self.scheduler_api.cluster_refresh(context)

def create_resource(ext_mgr):
    return wsgi.Resource(ClusterController(ext_mgr))

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

