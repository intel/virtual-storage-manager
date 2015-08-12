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
from django.views.generic import TemplateView
from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import views

from vsm_dashboard.api import vsm as vsmapi
from .tables import OsdsTable
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)

def device_get_smartinfo(request,device_id=None,device_path=None):
    search_opts = {}
    print 'device_id====',device_id,'--device_path=',device_path
    search_opts['device_id'] = device_id
    search_opts['device_path'] = device_path
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
        disk_near_full_threshold = int(settings['disk_near_full_threshold'])
        disk_full_threshold = int(settings['disk_full_threshold'])
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
                if osd['full_status'] >= disk_near_full_threshold and osd['full_status'] < disk_full_threshold:
                    osd['full_warn'] = 1
                elif osd['full_status'] >=disk_full_threshold:
                    osd['full_warn'] = 2
            else:
                osd['full_status'] = ''

            if osd_id == "-1":
                osds.append(osd)  #all of the deivces
            elif str(_osd.id) == str(osd_id):
                osds.append(osd)  #filter the devices by osd_id
            else:
                pass
        return osds


class AddOSDView(TemplateView):
    template_name = 'vsm/devices-management/add_osd.html'
    
    def get_context_data(self, **kwargs):
        context = {}
        storage_group_list = vsmapi.storage_group_status(None,)

        storage_group = []
        for _sg in storage_group_list:
            sg = {
                "id":_sg.id
                ,"storage_class":_sg.storage_class
            }
            storage_group.append(sg)
        context["storage_group"] = storage_group

        servers = vsmapi.get_server_list(None, )
        context["servers"] = servers;

        if len(servers) > 0:
            context["OSDList"] = vsmapi.osd_status(self.request, paginate_opts={
                "service_id": servers[0].service_id
            })
        
        return context

def get_smart_info(request):
    data = json.loads(request.body)

    device_data_dict = device_get_smartinfo(request,str(data["osd_id"]),data["device_path"])
    device_data_json = {
        "basic":{
             "DriveFamily":device_data_dict["basic"].get("Drive Family")
            ,"SerialNumber":device_data_dict["basic"].get("Serial Number")
            ,"FirmwareVersion":device_data_dict["basic"].get("Firmware Version")
            ,"DriveStatus":device_data_dict["basic"].get("Drive Status")
        }
        ,"smart":[]
    }

    for _smart_item in device_data_dict["smart"].iteritems():
        _item = {"key":_smart_item[0],"value":_smart_item[1]}
        device_data_json["smart"].append(_item)

    devicedata = json.dumps(device_data_json)
    return HttpResponse(devicedata)


def get_osd_list(request):
    data = json.loads(request.body)
    service_id = int(data["service_id"])
    osds = vsmapi.osd_status(None, paginate_opts={
                "service_id": service_id
            })

    osd_list = []
    for _osd in osds:
        osd = {
            "id":_osd.id
            ,"name":_osd.osd_name
            ,"weight":_osd.weight
            ,"storage_group":_osd.device['device_type']
            ,"journal":_osd.device['journal']
            ,"device":_osd.device['path']
        }
        print _osd
        osd_list.append(osd)


    osd_list_data_json = {"osdlist":osd_list}
    osd_list_data = json.dumps(osd_list_data_json)
    return HttpResponse(osd_list_data)


def add_new_osd_action(request):
    data = json.loads(request.body)
    vsmapi.add_new_disks_to_cluster(request,data)
    status_json = {"status":"OK"}
    status_data = json.dumps(status_json)
    return HttpResponse(status_data)

def check_device_path(request):
    search_opts = json.loads(request.body)
    server_id = search_opts["server_id"]
    data_device_path = search_opts["data_device_path"]
    journal_device_path = search_opts["journal_device_path"]


    ret = vsmapi.get_available_disks(request, search_opts={
                "server_id": server_id
                ,"path":[data_device_path,journal_device_path]
            })


    if ret["ret"] == 1 :
        status_json = {"status":"OK"}
    else:
        status_json = {"status":"Failed",'message':ret.get('message')}

    status_data = json.dumps(status_json)
    return HttpResponse(status_data)

