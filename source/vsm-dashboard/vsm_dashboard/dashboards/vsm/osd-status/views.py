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

import json
from django.http import HttpResponse
from django.views.generic import TemplateView
from horizon import tables
from vsm_dashboard.api import vsm as vsmapi
from vsm_dashboard.utils import get_time_delta
from .tables import ListOSDStatusTable

class ModalSummaryMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ModalSummaryMixin, self).get_context_data(**kwargs)
        return context

class IndexView(tables.DataTableView):
    table_class = ListOSDStatusTable
    template_name = 'vsm/osd-status/index.html'

    def get_data(self):
        keyword = self.request.GET.get("keyword","")
        pagerIndex = int(self.request.GET.get("pagerIndex",1))
        return get_datasource(pagerIndex,keyword)["osd_list"]

def calculate_paginate(page_index,osd_list_count):
    page_size = 20
    page_count = int(osd_list_count/page_size)
    page_mod = osd_list_count%page_size

    if page_mod > 0:
        page_count = page_count + 1
    pager_size = 10
    pager_count = int(page_count/(pager_size))
    pager_index = int(page_index/(pager_size))
    if page_count%pager_size > 0:
        pager_count = pager_count + 1
    if page_index%pager_size > 0:
        pager_index = pager_index + 1

    data_start_index = (page_index-1)*page_size
    data_end_index = data_start_index+page_size

    paginate = {
        "page_index":page_index,
        "page_count":page_count,
        "pager_index":pager_index,
        "pager_count":pager_count,
        "data_start_index":data_start_index,
        "data_end_index":data_end_index
    }
    return paginate

def get_datasource(page_index,keyword):
    paginate_opts = {
        "limit":10000,
        "marker":0,
        "sort_keys":'id',
        "sort_dir":'asc',
        "osd_name":keyword,
        "server_name":keyword,
        "zone_name":keyword,
        "state":keyword
    }
    #get the datasource
    datasource = vsmapi.osd_status_sort_and_filter(None,paginate_opts)
    #get the paginate
    paginate = calculate_paginate(page_index,len(datasource))

    #organize the data
    osd_data = {"osd_list":[],"paginate":paginate}
    index = 0
    for item in datasource:
        index += 1
        if index <= paginate['data_start_index'] or index > paginate['data_end_index']:
            continue
        capacity_total =  0 if not item.device['total_capacity_kb'] else int(item.device['total_capacity_kb']/1024)
        capacity_used = 0 if not item.device['used_capacity_kb'] else int(item.device['used_capacity_kb']/1024)
        capacity_avail = 0 if not item.device['avail_capacity_kb'] else int(item.device['avail_capacity_kb']/1024)
        capacity_percent_used = 0 if not item.device['total_capacity_kb'] else item.device['used_capacity_kb'] * 100 / item.device['total_capacity_kb']

        osd = {
            "id":item.id,
            "osd_name": item.osd_name,
            "vsm_status": item.operation_status,
            "osd_state": item.state,
            "crush_weight": item.weight,
            "capacity_total":capacity_total,
            "capacity_used":capacity_used,
            "capacity_avail":capacity_avail,
            "capacity_percent_used":capacity_percent_used, 
            "server": item.service['host'],
            "storage_group": item.storage_group['name'],
            "zone": item.zone,
            "updated_at": get_time_delta(item.updated_at),
            "deviceInfo":"",
            "page_index":paginate["page_index"],
            "page_count":paginate["page_count"],
            "pager_index":paginate["pager_index"],
            "pager_count":paginate["pager_count"],
        }

        osd_data["osd_list"].append(osd)
    
    return osd_data











