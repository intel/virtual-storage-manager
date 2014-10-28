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
from .tables import ListStorageGroupStatusTable
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)

from vsm_dashboard.common.horizon.chart import ChartRenderer

from django.utils.datastructures import SortedDict
from vsm_dashboard.utils import get_time_delta

class SGChart(ChartRenderer):
    name = "Storage Groups"

    def get_chart(self):
        _sgs = vsmapi.storage_group_status(self.request,)
        charts = []
        _cfg = vsmapi.get_setting_dict(self.request)
        for _sg in _sgs:
            _sg.capacity_total = 1 if not _sg.capacity_total else _sg.capacity_total
            capacity_percent_used = 0 if not _sg.capacity_total else _sg.capacity_used * 10000.0 / _sg.capacity_total / 100.0
            capacity_percent_used = round(capacity_percent_used, 2)
            capacity_percent_avail = 100 - capacity_percent_used
            if capacity_percent_used < int(_cfg["storage_group_near_full_threshold"]):
                index = 1
            elif capacity_percent_used < int(_cfg["storage_group_full_threshold"]):
                index = 4
            else:
                index = 7

            chart = {"type": "pie", "name": _sg.name,"verbose_name": _sg.name,
                     "used": capacity_percent_used,
                     "datas":[{"index": index,"value": capacity_percent_used},
                                          {"index":20,"value": capacity_percent_avail}]}
            charts.append(chart)

        return charts

class ModalChartMixin(object):

   def get_context_data(self, **kwargs):
        context = super(ModalChartMixin, self).get_context_data(**kwargs)
        context['chart'] = SGChart(self.request)
        context['settings'] = vsmapi.get_setting_dict(self.request)
        return context

class IndexView(ModalChartMixin, tables.DataTableView):
    table_class = ListStorageGroupStatusTable
    template_name = 'vsm/storage-group-status/index.html'

    def get_data(self):
        _sgs = []
        #_sgs= vsmapi.get_sg_list(self.request,)
        try:
            _sgs = vsmapi.storage_group_status(self.request,)
            if _sgs:
                logging.debug("resp body in view: %s" % _sgs)
            settings = vsmapi.get_setting_dict(self.request)
            sg_near_full_threshold = settings['storage_group_near_full_threshold']
            sg_full_threshold = settings['storage_group_full_threshold']
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve sever list. '))

        storage_group_status = []
        for _sg in _sgs:
            sg = {"id": _sg.id,
                        "name": _sg.name,
                        "attached_pools": _sg.attached_pools,
                        "capacity_total": 0 if not _sg.capacity_total else round(_sg.capacity_total * 1.0 / 1024 / 1024, 1),
                        "capacity_used": 0 if not _sg.capacity_used else round(_sg.capacity_used * 1.0 / 1024 / 1024, 1),
                        "capacity_avail": 0 if not _sg.capacity_avail else round(_sg.capacity_avail * 1.0 / 1024 / 1024, 1),
                        "capacity_percent_used": 0 if not _sg.capacity_total else _sg.capacity_used * 10000 / _sg.capacity_total / 100.0,
                        "largest_node_capacity_used": _sg.largest_node_capacity_used,
                        "largest_node_capacity_used": 0 if not _sg.largest_node_capacity_used else round(_sg.largest_node_capacity_used * 1.0 / 1024 / 1024, 1),
                        "status": _sg.status,
                        "updated_at": get_time_delta(_sg.updated_at),
                        }

            if sg['capacity_percent_used'] >= int(sg_full_threshold):
                sg['color'] = "red"
                sg['warning'] = "Storage Group Full Alert"
            elif sg['capacity_percent_used'] >= int(sg_near_full_threshold):
                sg['color'] = "#ff9933"
                sg['warning'] = "Storage Group Near Full Alert"
            else:
                sg['color'] = "black"
                sg['warning'] = ""

            storage_group_status.append(sg)
        return storage_group_status

