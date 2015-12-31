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
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django import forms as django_froms
from horizon import exceptions
from horizon import tables
from horizon import forms
from vsm_dashboard.api import vsm as vsmapi
from .tables import OsdsTable
from django.http import HttpResponse,HttpResponseRedirect

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
        if 'disk_near_full_threshold' not in settings.keys():
            vsmapi.update_setting(self.request,'disk_near_full_threshold','75')
        if 'disk_full_threshold' not in settings.keys():
            vsmapi.update_setting(self.request,'disk_full_threshold','85')
        disk_near_full_threshold = int(settings.get('disk_near_full_threshold',75))
        disk_full_threshold = int(settings.get('disk_full_threshold',85))
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

@csrf_exempt
def add_new_osd(request):
    template = "vsm/devices-management/add_osd.html"
    context = {}
    #get the server list
    servers = vsmapi.get_server_list(None, )
    context["servers"] = servers
    context["upload_file"] = UploadFileForm()
    context["storage_group"] = get_storage_group_list(request)
    context["osd_location"] = get_osd_location_list(request)

    #get the osd list from the file
    if request.method == "POST":
        form = UploadFileForm(request.POST,request.FILES)
        if form.is_valid():
            context["osd_list"] = handle_uploaded_file(request.FILES['file'])
            print 10 * "="
            print "the import osd list"
            print context["osd_list"]
            return render(request,template,context)
    return render(request,template,context)


def add_new_osd_action(request):
    data = json.loads(request.body)
    print 'data----7777==',data
    #vsmapi.add_new_disks_to_cluster(request,data)
    vsmapi.add_batch_new_disks_to_cluster(request,data)
    status_json = {"status":"OK"}
    status_data = json.dumps(status_json)
    return HttpResponse(status_data)

def get_storage_group_list(request):
    #get the storage group
    storage_group_list = vsmapi.storage_group_status(request)
    storage_group = []
    for _sg in storage_group_list:
        sg = {
            "id":_sg.id
            ,"name":_sg.name
        }
        storage_group.append(sg)
    return storage_group

def get_osd_location_list(request):
    zones = vsmapi.osd_locations_choices_by_type(request)
    osd_location_list = zones['osd_locations_choices']
    location_list = []
    print 'osd_location_list===',osd_location_list
    for location in osd_location_list:
        location_dict = {
            "id":location['id'],
            "name":location['name'],
        }
        location_list.append(location_dict)
    print 'location_list===',location_list
    return location_list

def get_osd_list_data(service_id):
    osd_list = vsmapi.osd_status(None, paginate_opts={
        "service_id": int(service_id)
    })
    return osd_list

class UploadFileForm(django_froms.Form):
    file = forms.FileField()

def handle_uploaded_file(f):
    osd_list = []
    try:
        #get the file content
        file_content = []
        for chunk in f.chunks():
           file_content.append(chunk)
        file_content = file_content[0].replace("\r\n",";").replace("\n",";").split(";");
        osd_list = generate_import_data_format(file_content)
    except Exception, e:
        print e
    return osd_list

def generate_import_data_format(file_content):
    osd_list = []
    for i,item in enumerate(file_content):
        #ignore the first line, there is no data
        if i == 0:
            continue
        #get the osd list
        osd = item.split(",")
        if len(osd) != 1:
            osd = {
                "server_name":osd[0],
                "sg_name":osd[1],
                "weight":osd[2],
                "journal":osd[3],
                "data":osd[4],
                "location":osd[5]
            }
            osd_list.append(osd)
    return osd_list



def DevicesAction(request, action):
    data = json.loads(request.body)

    device_data_str = device_get_smartinfo(request,str(data["osd_id"]))
    device_data_dict = {}
    device_data_str = device_data_str[0].device_data
    if device_data_str == None:
        devicedata = json.dumps({"data":""})
        return HttpResponse(devicedata)

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


def check_device_path(request):
    search_opts = json.loads(request.body)
    server_id = search_opts["server_id"]
    data_device_path = search_opts["data_device_path"]
    journal_device_path = search_opts["journal_device_path"]
    if data_device_path == journal_device_path:
        status_json = {"status":"Failed",'message':'data_device_path and journal_device_path can not be the same hard disk'}
    else:
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


def restart_osd(request):
    data = json.loads(request.body)
    osd_id_list = data["osd_id_list"]

    for osd_id in osd_id_list:
        vsmapi.osd_restart(request, osd_id)

    rs = json.dumps({"status":0})
    return HttpResponse(rs)

def get_available_disks(request):
    search_opts = json.loads(request.body)
    server_id = search_opts["server_id"]

    ret = vsmapi.get_available_disks(request, search_opts={
                "server_id": server_id
                ,"result_mode":"get_disks",
            })

    disks = ret['disks']
    if disks is None:disks=[]
    disk_data = json.dumps(disks)

    return HttpResponse(disk_data)

def remove_osd(request):
    data = json.loads(request.body)
    osd_id_list = data["osd_id_list"]

    for osd_id in osd_id_list:
        vsmapi.osd_remove(request, osd_id)

    rs = json.dumps({"status":0})
    return HttpResponse(rs)


def restore_osd(request):
    data = json.loads(request.body)
    osd_id_list = data["osd_id_list"]
    print osd_id_list

    for osd_id in osd_id_list:
        vsmapi.osd_restore(request, osd_id)

    rs = json.dumps({"status":0})
    return HttpResponse(rs)