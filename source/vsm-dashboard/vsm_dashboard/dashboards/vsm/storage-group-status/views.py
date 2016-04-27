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
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from vsm_dashboard.api import vsm as vsmapi
from .tables import ListStorageGroupStatusTable
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)

from vsm_dashboard.utils import get_time_delta



class ModalChartMixin(object):

   def get_context_data(self, **kwargs):
        context = super(ModalChartMixin, self).get_context_data(**kwargs)
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
                        "friendly_name": _sg.friendly_name,
                        "attached_pools": _sg.attached_pools,
                        "capacity_total": 0 if not _sg.capacity_total else round(_sg.capacity_total * 1.0 / 1024 / 1024, 1),
                        "capacity_used": 0 if not _sg.capacity_used else round(_sg.capacity_used * 1.0 / 1024 / 1024, 1),
                        "capacity_avail": 0 if not _sg.capacity_avail else round(_sg.capacity_avail * 1.0 / 1024 / 1024, 1),
                        "capacity_percent_used": 0 if not _sg.capacity_total else _sg.capacity_used * 10000 / _sg.capacity_total / 100.0,
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

#get pie charts data
def chart_data(request):
    charts = []
    _cfg = vsmapi.get_setting_dict(None)
    _sgs = vsmapi.storage_group_status(None)

    for _sg in _sgs:
        _sg.capacity_total = 1 if not _sg.capacity_total else _sg.capacity_total

        capacity_percent_used = 0 if not _sg.capacity_total else _sg.capacity_used * 10000.0 / _sg.capacity_total / 100.0
        capacity_percent_used = round(capacity_percent_used, 2)
        capacity_percent_avail = 100 - capacity_percent_used

        #0:normal;1:near full;2:full;  
        status = 0 
        if capacity_percent_used < int(_cfg["storage_group_near_full_threshold"]):
            status = 0
        elif capacity_percent_used < int(_cfg["storage_group_full_threshold"]):
            status = 1
        else:
            status = 2

        chart = {"id": _sg.id
                ,"name":_sg.name
                ,"status":status
                ,"used":capacity_percent_used
                ,"available":capacity_percent_avail}
        charts.append(chart)

    print charts

    chartsdata = json.dumps(charts)
    return HttpResponse(chartsdata)


