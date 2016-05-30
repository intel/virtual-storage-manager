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
from vsm.api.views import performance_metrics as performance_metrics_views
from vsm.openstack.common import jsonutils
from vsm import utils
from vsm import conductor
from vsm import scheduler
from vsm.scheduler import rpcapi as scheduler_rpcapi
from vsm import db
import time

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

class PerformanceMetricsController(wsgi.Controller):
    """The Servers API controller for the OpenStack API."""
    _view_builder_class = performance_metrics_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.scheduler_rpcapi = scheduler_rpcapi.SchedulerAPI()
        self.ext_mgr = ext_mgr
        super(PerformanceMetricsController, self).__init__()


    def get_list(self, req):
        """update cluster."""
        search_opts = {}
        search_opts.update(req.GET)
        context = req.environ['vsm.context']
        metrics = self.conductor_api.get_performance_metrics(context, search_opts=search_opts)
        LOG.info("CEPH_LOG get performance metrics by search opts: %s" % search_opts)
        return {"metrics": metrics}


    def get_metrics(self, req):
        LOG.info('time11111-metrics===%s'%time.time())
        search_opts = {}
        search_opts.update(req.GET)
        metrics_name =  search_opts['metrics_name']
        if metrics_name in ['op_r','op_w','op_rw','op_in_bytes','op_out_bytes']:
            result = self.get_iops_or_banwidth(req)
        elif metrics_name in ['op_rw_latency','op_r_latency','op_w_latency']:
            result = self.get_latency(req)
        elif  metrics_name in ["cpu_usage"]:
            result = self.get_cpu_usage(req)
        else:
            result = {"metrics":"no metric named %s data in DB"%metrics_name}
        LOG.info('time222-metrics===%s'%time.time())
        return result

    def get_iops_or_banwidth(self, req):
        """get_iops_or_banwidth."""
        search_opts = {}
        search_opts.update(req.GET)
        context = req.environ['vsm.context']
        search_opts ['metrics_name'] = 'osd_%s'%search_opts['metrics_name']
        metrics = db.get_sum_performance_metrics(context, search_opts=search_opts)
        LOG.info("CEPH_LOG get performance metrics  iops or banwidth  by search opts: %s" % search_opts)
        return {"metrics": metrics}

    def get_latency(self, req):
        """get_latency."""
        search_opts = {}
        search_opts.update(req.GET)
        context = req.environ['vsm.context']
        search_opts ['metrics_name'] = 'osd_%s'%search_opts['metrics_name']
        metrics = db.get_latency(context, search_opts=search_opts)
        LOG.info("CEPH_LOG get performance metrics  latency  by search opts: %s" % search_opts)
        return {"metrics": metrics}

    def get_metrics_all_types(self, req):
        #LOG.info('time333-metrics===%s'%time.time())
        search_opts = {}
        search_opts.update(req.GET)
        metrics_name = search_opts['metrics_name']
        context = req.environ['vsm.context']
        if metrics_name == 'iops':
            result = db.get_iops_all_types(context, search_opts=search_opts)
        elif metrics_name == 'lantency':
            result = db.get_latency_all_types(context, search_opts=search_opts)
        elif  metrics_name == 'bandwidth':
            result = db.get_bandwidth_all_types(context, search_opts=search_opts)
        elif  metrics_name in ["cpu_usage"]:
            result = self.get_cpu_usage(req)
        else:
            result = {"metrics":"no metric named %s data in DB"%metrics_name}
        #LOG.info('time4444-metrics===%s'%time.time())
        return result

    def get_cpu_usage(self, req):
        """get_cpu_usage"""
        search_opts = {}
        search_opts.update(req.GET)
        context = req.environ['vsm.context']
        search_opts ['metrics_name'] = search_opts['metrics_name']
        metrics = self.conductor_api.get_cpu_usage(context, search_opts=search_opts)
        LOG.info("CEPH_LOG get performance metrics  cpu_usage  by search opts: %s" % search_opts)
        return {"metrics": metrics}


def create_resource(ext_mgr):
    return wsgi.Resource(PerformanceMetricsController(ext_mgr))


