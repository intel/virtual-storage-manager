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
import json
from webob import exc
from vsm.api.openstack import wsgi
from vsm.api import xmlutil
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.api.views import summary as sum_views
from vsm import conductor
from vsm import scheduler
from vsm import db
from vsm import exception
from vsm import utils

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_vsm(elem, detailed=False):
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

vsm = make_vsm

vsm_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class VsmTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('vsm', selector='vsm')
        make_vsm(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=vsm_nsmap)

class VsmsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('vsms')
        elem = xmlutil.SubTemplateElement(root, 'vsms', selector='vsms')
        make_vsm(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=vsm_nsmap)

class Controller(wsgi.Controller):
    """The Vsm API controller for the OpenStack API."""

    def __init__(self, ext_mgr):
        super(Controller, self).__init__()

    def summary(self, req, cluster_id = None):
        LOG.info('vsm-summary.')
        context = req.environ['vsm.context']

        #TODO: as we have only one cluster for now, the cluster_id
        #has been hardcoded. In furture, client should pass
        # the cluster id by url.
        try:
            if cluster_id:
                vsm_sum = db.summary_get_by_cluster_id_and_type(context, cluster_id, 'vsm')
            else:
                vsm_sum = db.summary_get_by_type_first(context, 'vsm')
            #vsm_sum = db.summary_get_by_cluster_id_and_type(context, 1, 'vsm')
        except exception.SummaryNotFound:
            vsm_sum = None
        try:
            if cluster_id:
                ceph_sum = db.summary_get_by_cluster_id_and_type(context, cluster_id, 'ceph')
            else:
                ceph_sum = db.summary_get_by_type_first(context, 'ceph')
            #ceph_sum = db.summary_get_by_cluster_id_and_type(context, 1, 'ceph')
        except exception.SummaryNotFound:
            ceph_sum = None

        get_data = lambda x: x['summary_data'] if x else None

        sum = None
        vsm_data = get_data(vsm_sum)
        ceph_data = get_data(ceph_sum)

        if vsm_data:
            sum = json.loads(vsm_data)
            if ceph_data:
                sum.update(json.loads(ceph_data))
            else:
                sum['is_ceph_active'] = True
        elif ceph_data:
            sum = json.loads(ceph_data)
            if not vsm_data:
                sum['uptime'] = None

        if sum:
            try:
                sum['created_at'] = vsm_sum['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                sum_data = {
                    'summary_data': json.dumps(sum)
                }
            except:
                pass
        else:
            sum_data = None

        LOG.info('vsm sum: %s' % sum_data)
        return sum_views.ViewBuilder().basic(sum_data, 'vsm')

def create_resource(ext_mgr):
    return wsgi.Resource(Controller(ext_mgr))

