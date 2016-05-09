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
from vsm.agent import cephconfigparser

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_cluster(elem, detailed=False):
    elem.set('id')
    elem.set('name')
    elem.set('file_system')
    elem.set('journal_size')
    elem.set('size')
    elem.set('management_network')
    elem.set('ceph_public_network')
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

        # only and should only one mds
        mds_count = 0
        for server in server_list:
            if server['is_mds'] == True:
                mds_count = mds_count + 1
        if mds_count > 1:
            raise exc.HTTPBadRequest("More than one mds.")

        # only and should only one rgw
        rgw_count = 0
        for server in server_list:
            if server['is_rgw'] == True:
                rgw_count = rgw_count + 1
        if rgw_count > 1:
            raise exc.HTTPBadRequest("More than one rgw.")

        self.scheduler_api.create_cluster(context, server_list)
        return webob.Response(status_int=202)

    def import_ceph_conf(self, req, body=None):
        """
        import_ceph_conf to db and ceph nodes
        """
        LOG.info("CEPH_LOG import_ceph_conf body=%s"%body )
        context = req.environ['vsm.context']
        ceph_conf_path = body["cluster"]["ceph_conf_path"]
        cluster_name = body["cluster"]["cluster_name"]
        cluster = db.cluster_get_by_name(context,cluster_name)
        if cluster:
            ceph_conf_dict_old = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)._parser.as_dict()
            ceph_conf_parser = cephconfigparser.CephConfigParser(ceph_conf_path)._parser
            ceph_conf_dict = ceph_conf_parser.as_dict()
            check_ret = check_ceph_conf(ceph_conf_dict_old,ceph_conf_dict)
            if check_ret:
                return {"message":"%s"%check_ret}
            self.scheduler_api.import_ceph_conf(context,cluster_id=cluster.id,ceph_conf_path=ceph_conf_path)
            return {"message":"Success"}
        else:
            return {"message":"No such cluster which named  %s in DB"%cluster_name}

    def detect_cephconf(self, req, body=None):
        '''

        :param res:
        :param body:
        :return:
        '''
        LOG.info("CEPH_LOG detect_cephconf body=%s"%body )
        context = req.environ['vsm.context']
        ret = self.scheduler_api.detect_cephconf(context,body)
        LOG.info('CEPH_LOG detect_cephconf get ret=%s'%ret)
        return ret

    def detect_crushmap(self, req, body=None):
        '''

        :param res:
        :param body:
        :return:
        '''
        LOG.info("CEPH_LOG detect_crushmap body=%s"%body )
        context = req.environ['vsm.context']
        ret = self.scheduler_api.detect_crushmap(context,body)
        LOG.info('CEPH_LOG detect_crushmap get ret=%s'%ret)
        return ret

    def get_crushmap_tree_data(self, req, body=None):
        '''

        :param res:
        :param body:
        :return:
        '''
        LOG.info("CEPH_LOG get_crushmap_tree_data body=%s"%body )
        context = req.environ['vsm.context']
        ret = self.scheduler_api.get_crushmap_tree_data(context,body)
        LOG.info('CEPH_LOG get_crushmap_tree_data get ret=%s'%ret)
        return ret

    def check_pre_existing_cluster(self,req,body):
        '''

        :param res:
        :param body:
        :return:
        '''
        LOG.info("CEPH_LOG check_pre_existing_cluster body=%s"%body )
        context = req.environ['vsm.context']
        ret = self.scheduler_api.check_pre_existing_cluster(context,body)
        LOG.info('CEPH_LOG check_pre_existing_cluster get ret=%s'%ret)
        return ret

    def import_cluster(self,req,body):
        '''

        :param res:
        :param body:
        :return:
        '''
        LOG.info("CEPH_LOG import_cluster body=%s"%body )
        context = req.environ['vsm.context']
        ret = self.scheduler_api.import_cluster(context,body)
        LOG.info('CEPH_LOG import_cluster get ret=%s'%ret)
        return ret

    def integrate(self, req,body=None):
        """
        integrate an existing ceph cluster
        """
        LOG.info("CEPH_LOG cluster integrate body" )
        context = req.environ['vsm.context']
        #server_list = body['cluster']['servers']
        LOG.info('Begin to call scheduler.integrate_cluster')
        self.scheduler_api.integrate_cluster(context)

    def start_cluster(self, req, body=None):
        """
        start_cluster
        """
        LOG.info("CEPH_LOG start_cluster body=%s"%body )
        context = req.environ['vsm.context']
        cluster_id = body["cluster"]["id"]
        if cluster_id:
            nodes = db.init_node_get_by_cluster_id(context,cluster_id)
        else:
            nodes = db.init_node_get_all(context)
        servers = {"servers":nodes}
        self.scheduler_api.start_cluster(context,servers)
        return {"message":"Success"}

    def stop_cluster(self, req, body=None):
        """
        stop_cluster
        """
        LOG.info("CEPH_LOG stop_cluster body=%s"%body )
        context = req.environ['vsm.context']
        cluster_id = body["cluster"]["id"]
        if cluster_id:
            nodes = db.init_node_get_by_cluster_id(context,cluster_id)
        else:
            nodes = db.init_node_get_all(context)
        servers = {"servers":nodes}
        self.scheduler_api.stop_cluster(context,servers)
        return {"message":"Success"}

    def get_ceph_health_list(self, req):
        context = req.environ['vsm.context']
        ceph_status = self.scheduler_api.get_ceph_health_list(context)
        return {"ceph_status":ceph_status}

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

    def summary(self, req,cluster_id=None):
        #LOG.info('osd-summary body %s ' % body)
        context = req.environ['vsm.context']
        #TODO: as we have only one cluster for now, the cluster_id
        #has been hardcoded. In furture, client should pass
        # the cluster id by url.
        if cluster_id:
            sum = db.summary_get_by_cluster_id_and_type(context, cluster_id, 'cluster')
        else:
            sum = db.summary_get_by_type_first(context, 'cluster')
        vb = summary_view.ViewBuilder()
        return vb.basic(sum, 'cluster')

    def get_service_list(self, req,cluster_id=None):
        context = req.environ['vsm.context']
        service = db.service_get_all(context)
        return {"services":service}

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

def check_ceph_conf(ceph_conf_dict_old,ceph_conf_dict):
    check_result = ''
    keys_old = ceph_conf_dict_old.keys()
    keys_new = ceph_conf_dict.keys()
    old_osds = [key  for key in keys_old if key.find("osd.")!=-1]
    old_mons = [key  for key in keys_old if key.find("mon.")!=-1]
    old_mds = [key  for key in keys_old if key.find("mds.")!=-1]
    new_osds = [key  for key in keys_new if key.find("osd.")!=-1]
    new_mons = [key  for key in keys_new if key.find("mon.")!=-1]
    new_mds = [key  for key in keys_new if key.find("mds.")!=-1]
    if set(old_osds) != set(new_osds):
        check_result = '%s\n.error:The number of osd is different from the old version'%check_result
    if set(old_mons) != set(new_mons):
        check_result = '%s\n.error:The number of mon is different from the old version'%check_result
    if set(old_mds) != set(new_mds):
        check_result = '%s\n.error:The number of mds is different from the old version'%check_result
    if check_result:
        return check_result
    try:
        osd_field_to_check = ["osd journal","devs","host","cluster addr","public addr"]
        for osd in new_osds:
            for field in osd_field_to_check:
                if ceph_conf_dict[osd][field]!= ceph_conf_dict_old[osd][field]:
                   check_result = '%s\n.error:the value of %s below section %s'%(check_result,field,osd)
        mon_field_to_check = ['mon addr','host']
        for mon in new_mons:
            for field in mon_field_to_check:
                if ceph_conf_dict[mon][field]!= ceph_conf_dict_old[mon][field]:
                   check_result = '%s\n.error:the value of %s below section %s'%(check_result,field,mon)
        mds_field_to_check = ['public addr','host']
        for mds in new_mds:
            for field in mds_field_to_check:
                if ceph_conf_dict[mds][field]!= ceph_conf_dict_old[mds][field]:
                   check_result = '%s\n.error:the value of %s below section %s'%(check_result,field,mds)
    except Exception,e:
        check_result = '%s\n.error:KeyError :%s'%(check_result,e)
    return check_result
