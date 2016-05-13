#  Copyright 2014 Intel Corporation, All Rights Reserved.
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

"""
Performance Metrics interface.
"""

import urllib
from vsmclient import base


class PerformanceMetrics(base.Resource):
    """Performance metrics of ceph cluster and server of cpu, memory and so on."""
    def __repr__(self):
        return "<PerformanceMetrics: %s>" % self.id

class PerformanceMetricsManager(base.ManagerWithFind):
    """
    Manage :class:`Server` resources.
    """
    resource_class = PerformanceMetrics

    def list(self, search_opts=None):
        """
        Get a list of .
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        ret = self._list("/performance_metrics/get_list%s" % (query_string),"performance_metrics")
        return ret

    def get_metrics(self, search_opts=None):
        """
        Get a list of metrics by metrics name and timestamp.
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        #ret = self._list("/performance_metrics/get_metrics%s" % (query_string),"metrics")
        resp, body = self.api.client.get("/performance_metrics/get_metrics%s" % (query_string))
        return body

    def get_metrics_all_types(self, search_opts=None):
        """
        Get a list of metrics by metrics name and timestamp.
        """
        if search_opts is None:
            search_opts = {}

        qparams = {}

        for opt, val in search_opts.iteritems():
            if val:
                qparams[opt] = val

        query_string = "?%s" % urllib.urlencode(qparams) if qparams else ""

        #ret = self._list("/performance_metrics/get_metrics%s" % (query_string),"metrics")
        resp, body = self.api.client.get("/performance_metrics/get_metrics_all_types%s" % (query_string))
        return body


