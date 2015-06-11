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
import os
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy

from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import views

from vsm_dashboard.api import vsm as vsmapi
from .tables import ListMonitorStatusTable
from django.http import HttpResponse
from vsm_dashboard.common.horizon.summary import SummaryRenderer

import json
LOG = logging.getLogger(__name__)

from django.utils.datastructures import SortedDict
from vsm_dashboard.utils import get_time_delta

class ModalSummaryMixin(object):

    def get_context_data(self, **kwargs):
        context = super(ModalSummaryMixin, self).get_context_data(**kwargs)
        return context

class IndexView(ModalSummaryMixin, tables.DataTableView):
    table_class = ListMonitorStatusTable
    template_name = 'vsm/monitor-status/index.html'

    def get_data(self):
        _monitor_status = []
        #_monitors= vsmapi.get_monitor_list(self.request,)
        try:
            _monitor_status = vsmapi.monitor_status(self.request,)
            LOG.info("MONITOR STATUS: %s "%_monitor_status)
            #LOG.error(_monitor_status)
            #LOG.error("")
            if _monitor_status:
                logging.debug("resp body in view: %s" % _monitor_status)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve mon list. '))

        monitor_status = []
        for _monitor in _monitor_status:
            monitor = {"id": _monitor.id,
                        "name": _monitor.name,
                        "address": _monitor.address,
                        "health": _monitor.health,
                        "details": _monitor.details,
                        "skew": _monitor.skew,
                        "latency": _monitor.latency,
                        "mb_total": 0 if not _monitor.kb_total else int(_monitor.kb_total/1024),
                        "mb_used": 0 if not _monitor.kb_used else int(_monitor.kb_used/1024),
                        "mb_avail": 0 if not _monitor.kb_avail else int(_monitor.kb_avail/1024),
                        "percent_avail": _monitor.avail_percent,
                        "updated_at": get_time_delta(_monitor.updated_at),
                      }

            monitor_status.append(monitor)
        return monitor_status

