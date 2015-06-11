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
import sys
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy
from django.utils.datastructures import SortedDict
from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import views

from vsm_dashboard.api import vsm as vsmapi
from .tables import OsdsTable
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)

def device_get_smartinfo(request,device_id=None,action='get_smart_info'):
    search_opts = {}
    #print 'device_id====',device_id
    if device_id:search_opts['device_id'] = device_id
    search_opts['action'] = action
    ret = vsmapi.device_get_smartinfo(request,search_opts=search_opts)
    return ret

class IndexView(tables.DataTableView):
    table_class = OsdsTable
    template_name = 'vsm/devices-management/index.html'

    def get_data(self):
        default_limit = 10000;
        default_sort_dir = "asc";
        default_sort_keys = ['osd_name']
        marker = self.request.GET.get('marker', "")
        osd_id = self.request.GET.get('osdid',"-1")
        try:
            _osds = vsmapi.osd_status(self.request, paginate_opts={
                "limit": default_limit,
                "sort_dir": default_sort_dir,
                "marker":   marker,
            })
        except:
            _osds = []
            exceptions.handle(self.request,
                              _('Unable to retrieve osds. '))
        if _osds:
            logging.debug("resp osds in view: %s" % _osds)
        osds = []
        settings = vsmapi.get_setting_dict(self.request)
        disk_near_full_threshold = settings['disk_near_full_threshold']
        disk_full_threshold = settings['disk_full_threshold']
        for _osd in _osds:
            osd = {
                    'id': _osd.id,
                    'osd': _osd.osd_name,
                    'vsm_status': _osd.operation_status,
                    'osd_state': _osd.state,
                    'osd_weight': _osd.weight,
                    'storage_group': _osd.device['device_type'],
                    'data_dev_path': _osd.device['path'],
                    'data_dev_status': _osd.device['state'],
                    'data_dev_capacity': 0 if not _osd.device['total_capacity_kb']\
            else int(_osd.device['total_capacity_kb']/1024),
                    'data_dev_used': 0 if not _osd.device['used_capacity_kb']\
            else int(_osd.device['used_capacity_kb']/1024),
                    'data_dev_available': 0 if not _osd.device['avail_capacity_kb']\
            else int(_osd.device['avail_capacity_kb']/1024),
                    'journal_device_path': _osd.device['journal'],
                    'journal_device_status': _osd.device['journal_state'], 
                    'server': _osd.service['host'],
                    'zone': _osd.zone,
                    'full_warn': 0
                  }

            if osd['data_dev_capacity']:
                osd['full_status'] = round(osd['data_dev_used'] * 1.0 / osd['data_dev_capacity'] * 100, 2)
            else:
                osd['full_status'] = ''
            if osd['full_status'] >= disk_near_full_threshold and osd['full_status'] < disk_full_threshold:
                osd['full_warn'] = 1
            elif osd['full_status'] >=disk_full_threshold:
                osd['full_warn'] = 2
            if osd_id == "-1":
                osds.append(osd)  #all of the deivces
            elif str(_osd.id) == str(osd_id):
                osds.append(osd)  #filter the devices by osd_id
            else:
                pass
        return osds


def DevicesAction(request, action):
    data = json.loads(request.body)
    device_data_str = device_get_smartinfo(request,str(data["osd_id"]))
    device_data_dict = {}
    device_data_str = device_data_str[0].device_data
    for data in device_data_str.split("\n"):
        data_list = data.split("=")
        data_list_len = len(data_list)
        if data_list_len == 1:
            device_data_dict[data_list[0]] = ""
        if data_list_len == 2:
            device_data_dict[data_list[0]] = data_list[1]
    device_data_json = {
                "basic":{"status":device_data_dict["Drive Status"],
                       "family":device_data_dict["Drive Family"],
                       "seriesNumber":device_data_dict["Serial Number"],
                       "firmware":device_data_dict["Firmware"],
                       "totalCapacity":device_data_dict["Capacity in total"],
                       "usedCapacity":device_data_dict["Capacity in use"],
                },
                "smart":{"percentageUsed":device_data_dict["Percentage Used"],
                       "temperature":device_data_dict["Temperature"],
                       "unitRead":str(int(device_data_dict["Data Units Read"],16)),
                       "unitWRITE":device_data_dict["Data Units Written"],
                }
    }

    devicedata = json.dumps(device_data_json)
    return HttpResponse(devicedata)
