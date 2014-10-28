# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Openstack, LLC
# Copyright 2012 Nebula, Inc.
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
from .tables import ListPGStatusTable
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)

from django.views.generic import TemplateView
from vsm_dashboard.dashboards.vsm.overview.summarys import PGSummary
from vsm_dashboard.dashboards.vsm.overview.summarys import CapacitySummary
from vsm_dashboard.dashboards.vsm.overview.summarys import PerformanceSummary
from vsm_dashboard.dashboards.vsm.overview.summarys import ObjectSummary

class ModalSummaryMixin(object):

   def get_context_data(self, **kwargs):
        context = super(ModalSummaryMixin, self).get_context_data(**kwargs)
        context['pg_summary'] = PGSummary(self.request)
        context['performance_summary'] = PerformanceSummary(self.request)
        context['object_summary'] = ObjectSummary(self.request)
        context['capacity_summary'] = CapacitySummary(self.request)
        return context

class IndexView(ModalSummaryMixin, tables.DataTableView):
    table_class = ListPGStatusTable
    template_name = 'vsm/pg-status/index.html'

    def get_data(self):
        default_limit = 100;
        default_sort_dir = "asc";
        default_sort_keys = ['pgid']
        marker = self.request.GET.get('marker', "")

        _pg_status= []
        #_pgs= vsmapi.get_pg_list(self.request,)
        try:
            _pg_status = vsmapi.placement_group_status(self.request, paginate_opts={
                "limit": default_limit,
                "sort_dir": default_sort_dir,
                "marker":   marker,
            })
            if _pg_status:
                logging.debug("resp body in view: %s" % _pg_status)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve sever list. '))

        pg_status = []
        for _pg in _pg_status:
            pg = {"id": _pg.id,
                        "pg_id": _pg.pg_id,
                        "state": _pg.state,
                        "up": _pg.up,
                        "acting": _pg.acting,
                        }

            pg_status.append(pg)
        return pg_status

class SummaryView(ModalSummaryMixin, TemplateView):
    template_name = 'vsm/pg-status/index.html'

