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

from __future__ import division
import logging

from django.views.generic import TemplateView
from django.http import HttpResponse
from vsm_dashboard.api import vsm as vsmapi
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from vsm_dashboard.utils import get_time_delta
from vsm_dashboard.utils import get_time_delta2
import json
import random
import datetime
LOG = logging.getLogger(__name__)


class ModalSummaryMixin(object):

    def get_context_data(self, **kwargs):
        context = super(ModalSummaryMixin, self).get_context_data(**kwargs)
        return context

class IndexView(ModalSummaryMixin, TemplateView):
    template_name = 'vsm/overview/index.html'


#handle the vsm_version
def version(request):
    return HttpResponse(get_version())

#handle the cluster data
def cluster(request):
    return HttpResponse(get_cluster())

#handle the capactiy data
def capacity(request):
    return HttpResponse(get_capacity())

#handle the OSD data
def OSD(request):
    return HttpResponse(get_OSD())

#handle the monitor data
def monitor(request):
    return HttpResponse(get_monitor())

#handle the MDS data
def MDS(request):
    return HttpResponse(get_MDS())

#handle the storage data
def storage(request):
    return HttpResponse(get_storage())

#handle the pg data
def PG(request):
    return HttpResponse(get_PG())

def IOPS(request):
    IOPS_dict = {"line1":random.randint(0,15)
                ,"line2":random.randint(0,15)}
    IOPSdata = json.dumps(IOPS_dict)
    return HttpResponse(IOPSdata)


#get the vsm_version
def get_version():
    vsm_summary = vsmapi.vsm_summary(None)
    vsm_version = { "version":"2015.01-1.0.el6"
                   , "update": get_time_delta2(vsm_summary.created_at)}
    versiondata = json.dumps(vsm_version)
    return versiondata


#get the cluster data
def get_cluster():
    cluster_summary = vsmapi.cluster_summary(None)
    cluster_name = vsmapi.get_cluster_list(None)[1]['clusters'][0]['name']
    #HEALTH_OK HEALTH_WARN  HEALTH_ERROR
    cluster_status = cluster_summary.health_list[0]
    cluster_note = []
    if cluster_status == "HEALTH_OK":
        for note in cluster_summary.health_list[1:]:
            cluster_note.append(note)
    else:
        for index, note in enumerate(cluster_summary.detail):
            cluster_note.append(note)

    vsm_status_dict = { "name":cluster_name
                      , "status": cluster_status
                      , "note":cluster_note}
    vsmstatusdata = json.dumps(vsm_status_dict)
    return vsmstatusdata

#get the capactiy data
def get_capacity():
    pg_summary = vsmapi.placement_group_summary(None)
    used_percent = ('%.2f'%((pg_summary.bytes_used/pg_summary.bytes_total)*100)); 
    capacity_dict = {"value":used_percent}
    capacitydata = json.dumps(capacity_dict)
    return capacitydata

#get the OSD data
def get_OSD():
    in_up = 0
    in_down = 0
    out_up = 0
    out_down = 0
    osd_summary = vsmapi.osd_summary(None)
    _osd_status = vsmapi.osd_status(None)
    for _osd in _osd_status:
        print _osd.state
        if _osd.state == "In-Up":
            in_up=in_up+1
        elif _osd.state == "In-Down":
            in_dowm=in_down+1
        elif _osd.state == "Out-Up":
            out_up=out_up+1
        elif _osd.state == "Out-Down":
            out_down=out_down+1
    
    OSD_dict = {"epoch":osd_summary.epoch
              ,"update":get_time_delta(osd_summary.updated_at)
              ,"in_up":in_up
              ,"in_down":in_down
              ,"out_up":out_up
              ,"out_down":out_down
              }
    OSDdata = json.dumps(OSD_dict)
    return OSDdata

#get the monitor data
def get_monitor():
    monitor_summary = vsmapi.monitor_summary(None)
    epoch = monitor_summary.monmap_epoch
    update = get_time_delta(monitor_summary.updated_at)
    quorumlist = monitor_summary.quorum.split(" ")
    #monitors = monitor_summary.monitors

    Monitor_dict = {"epoch":epoch
              ,"update":update
              ,"quorum":quorumlist
              ,"selMonitor":1}
    Monitordata = json.dumps(Monitor_dict)
    return Monitordata

#get the MDS data
def get_MDS():
    mds_summary = vsmapi.mds_summary(None)
    ecpoch = mds_summary.epoch
    Up = mds_summary.num_up_mdses
    In = mds_summary.num_in_mdses
    Failed = mds_summary.num_failed_mdses
    Stopped = mds_summary.num_stopped_mdses

    mds_status = vsmapi.mds_status(None)
    update = ""
    for mds in mds_status:
        update = get_time_delta(mds.updated_at)

    MDS_dict = {"epoch":ecpoch
              ,"update":update
              ,"Up":Up
              ,"In":In
              ,"Failed":Failed
              ,"Stopped":Stopped
              ,"PoolData":"--"
              ,"MetaData":"--"}
    MDSdata = json.dumps(MDS_dict)
    return MDSdata

#get the storage data
def get_storage():
    _sgs = vsmapi.storage_group_status(None)
    _cfg = {"nearfull_threshold":65,
            "full_threshold":85,}
    _num = 0
    _num_normal = 0
    _num_near_full = 0
    _num_full = 0
    for _sg in _sgs:
        _sg.capacity_total = 1 if not _sg.capacity_total else _sg.capacity_total
        capcity_percent_used = 0 if not _sg.capacity_total else _sg.capacity_used * 100 / _sg.capacity_total
        if capcity_percent_used <_cfg["nearfull_threshold"]:
            _num_normal+=1
        elif capcity_percent_used < _cfg["full_threshold"]:
            _num_near_full+=1
        else:
            _num_full+=1
        _num+=1

    Storage_dict = {"nearfull":_num_near_full
                   ,"full":_num_full
                   ,"normal":_num_normal
                   ,"update":get_time_delta(_sgs[0].updated_at)}

    storagedata = json.dumps(Storage_dict)
    return storagedata

#get the PG data
def get_PG():
    pg_summary = vsmapi.placement_group_summary(None)
    version = pg_summary.version
    update = get_time_delta(pg_summary.updated_at)
    pg_total = pg_summary.num_pgs
    pg_active_clean = sum([pgs['count'] for pgs in pg_summary.pgs_by_state
                                        if pgs['state_name'] == "active+clean"])
    pg_not_active_clean = sum([pgs['count'] for pgs in pg_summary.pgs_by_state
                                        if pgs['state_name'] != "active+clean"])  
    pg_dict = {"version":version
              ,"update":update
              ,"total":pg_total
              ,"active_clean":pg_active_clean
              ,"not_active_clean":pg_not_active_clean}
    pgdata = json.dumps(pg_dict)
    return pgdata


