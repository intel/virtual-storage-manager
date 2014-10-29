# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Corporation, All Rights Reserved.
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

import logging

from django.views.generic import TemplateView

LOG = logging.getLogger(__name__)

from .summarys import ClusterSummary
from .summarys import WarningSummary
from .summarys import StorageGroupSummary
from .summarys import VsmSummary
from .summarys import MonitorSummary
from .summarys import OsdSummary
from .summarys import MdsSummary
from .summarys import PGSummaryDashboard
from .summarys import ClusterHealthSummary

class ModalSummaryMixin(object):

    def get_context_data(self, **kwargs):
        context = super(ModalSummaryMixin, self).get_context_data(**kwargs)
        context['cluster_summary'] = ClusterSummary(self.request)
        context['warning_summary'] = WarningSummary(self.request)
        context['sg_summary'] = StorageGroupSummary(self.request)
        context['vsm_summary'] = VsmSummary(self.request)
        context['monitor_summary'] = MonitorSummary(self.request)
        context['mds_summary'] = OsdSummary(self.request)
        context['osd_summary'] = MdsSummary(self.request)
        context['pg_summary'] = PGSummaryDashboard(self.request)
        context['cluster_health_summary'] = ClusterHealthSummary(self.request)
        return context

class IndexView(ModalSummaryMixin, TemplateView):
    template_name = 'vsm/overview/index.html'

