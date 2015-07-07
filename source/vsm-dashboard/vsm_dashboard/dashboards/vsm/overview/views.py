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
import summarys
import json
import random
import datetime
import commands
import time
LOG = logging.getLogger(__name__)


class ModalSummaryMixin(object):

    def get_context_data(self, **kwargs):
        context = super(ModalSummaryMixin, self).get_context_data(**kwargs)
        return context

class IndexView(ModalSummaryMixin, TemplateView):
    template_name = 'vsm/overview/index.html'

#show osd summary
def osd_summary(request):
    return HttpResponse(json.dumps(summarys.osd()))

#show monitor summary
def monitor_summary(request):
    return HttpResponse(json.dumps(summarys.monitor()))

#show mds summary
def mds_summary(request):
    return HttpResponse(json.dumps(summarys.mds()))

#show objects summary
def objects_summary(request):
    return HttpResponse(json.dumps(summarys.objects()))

#show performance summary
def performance_summary(request):
    return HttpResponse(json.dumps(summarys.performance()))

#show pg summary
def pg_summary(request):
    return HttpResponse(json.dumps(summarys.pg()))

#show capacity summary
def capacity_summary(request):
    return HttpResponse(json.dumps(summarys.capactiy()))



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
    # data = json.loads(request.body)
    # timestamp = int(data["timestamp"])
    return HttpResponse(get_performance_IOPs())

def latency(request):
    # data = json.loads(request.body)
    # timestamp = int(data["timestamp"])
    return HttpResponse(get_performance_Latency())

def bandwidth(request):
    # data = json.loads(request.body)
    # timestamp = int(data["timestamp"])
    return HttpResponse(get_performance_Bandwith())


def get_vsm_version():
    try:
        (status, out) = commands.getstatusoutput('vsm --version')
        print "get_vsm_version:%s--%s"%(out,status)
    except:
        out = '2.0'
    return out

#get the vsm_version
def get_version():
    vsm_version = get_vsm_version()
    try:
        vsm_summary = vsmapi.vsm_summary(None)
        uptime = get_time_delta2(vsm_summary.created_at)
        ceph_version = vsm_summary.ceph_version
    except:
        uptime = ''
    vsm_version = { "version": vsm_version,
                    "update": uptime,
                    "ceph_version":ceph_version}
    versiondata = json.dumps(vsm_version)
    return versiondata

#get the cluster data
def get_cluster():
    cluster_summary = vsmapi.cluster_summary(None)
    cluster_name = vsmapi.get_cluster_list(None)[1]['clusters'][0]['name']
    #HEALTH_OK HEALTH_WARN  HEALTH_ERROR
    cluster_status = cluster_summary.health_list[0]
    cluster_note = []
    for note in cluster_summary.health_list[1:]:
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
    PoolData = mds_summary.data_pools
    MetaData = mds_summary.metadata_pool

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
              ,"PoolData":PoolData
              ,"MetaData":MetaData}
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

def get_performance_IOPs():
    end_time = int(time.time())
    start_time = end_time - 15
    # end_time = timestamp + 15
    # start_time = timestamp 

    ops_r_opts = {
         "metrics_name":"ops_r"
        ,"timestamp_start":start_time
        ,"timestamp_end":end_time
        ,"correct_cnt":None
    }

    ops_w_opts = {
         "metrics_name":"ops_w"
        ,"timestamp_start":start_time
        ,"timestamp_end":end_time
        ,"correct_cnt":None
    }

    ops_r_data = vsmapi.get_performance_metrics(None,ops_r_opts)["metrics"]
    ops_w_data = vsmapi.get_performance_metrics(None,ops_w_opts)["metrics"]


    metriclist = []
    for r_metric in ops_r_data:
        item = {"timestamp":r_metric["timestamp"],"r_value":r_metric["metrics_value"],"w_value":""}
        metriclist.append(item)

    for item in metriclist:
        for w_metric in ops_w_data:
            if item["timestamp"] == w_metric["timestamp"]:
                item["w_value"] = w_metric["metrics_value"]
                break

    ops_data_dict = {"metrics":metriclist}
    ops_data = json.dumps(ops_data_dict)
    return ops_data

def get_performance_Latency():
    end_time = int(time.time())
    start_time = end_time - 15
    # end_time = timestamp + 15
    # start_time = timestamp 

    latency_r_opts = {
         "metrics_name":"latency_r"
        ,"timestamp_start":start_time
        ,"timestamp_end":end_time
        ,"correct_cnt":None
    }

    latency_w_opts = {
         "metrics_name":"latency_w"
        ,"timestamp_start":start_time
        ,"timestamp_end":end_time
        ,"correct_cnt":None
    }

    latency_rw_opts = {
         "metrics_name":"latency_rw"
        ,"timestamp_start":start_time
        ,"timestamp_end":end_time
        ,"correct_cnt":None
    }

    latency_r_data = vsmapi.get_performance_metrics(None,latency_r_opts)["metrics"]
    latency_w_data = vsmapi.get_performance_metrics(None,latency_w_opts)["metrics"]
    latency_rw_data = vsmapi.get_performance_metrics(None,latency_rw_opts)["metrics"]


    metriclist = []
    for r_metric in latency_r_data:
        item = {"timestamp":r_metric["timestamp"],"r_value":r_metric["metrics_value"],"w_value":"","rw_value":""}
        metriclist.append(item)

    for item in metriclist:
        for w_metric in latency_w_data:
            if item["timestamp"] == w_metric["timestamp"]:
                item["w_value"] = w_metric["metrics_value"]
                break
        for rw_metric in latency_rw_data:
            if item["timestamp"] == rw_metric["timestamp"]:
                item["rw_value"] = rw_metric["metrics_value"]
                break

    ops_data_dict = {"metrics":metriclist}
    ops_data = json.dumps(ops_data_dict)
    return ops_data


def get_performance_Bandwith():
    end_time = int(time.time())
    start_time = end_time - 15
    # end_time = timestamp + 15
    # start_time = timestamp 

    bandwidth_in_opts = {
         "metrics_name":"bandwidth_in"
        ,"timestamp_start":start_time
        ,"timestamp_end":end_time
        ,"correct_cnt":None
    }

    bandwidth_out_opts = {
         "metrics_name":"bandwidth_out"
        ,"timestamp_start":start_time
        ,"timestamp_end":end_time
        ,"correct_cnt":None
    }


    bandwidth_in_data = vsmapi.get_performance_metrics(None,bandwidth_in_opts)["metrics"]
    bandwidth_out_data = vsmapi.get_performance_metrics(None,bandwidth_out_opts)["metrics"]

    metriclist = []
    for in_metric in bandwidth_in_data:
        item = {"timestamp":in_metric["timestamp"],"in_value":in_metric["metrics_value"],"out_value":""}
        metriclist.append(item)

    for item in metriclist:
        for out_metric in bandwidth_out_data:
            if item["timestamp"] == out_metric["timestamp"]:
                item["out_value"] = out_metric["metrics_value"]
                break


    ops_data_dict = {"metrics":metriclist}
    ops_data = json.dumps(ops_data_dict)
    return ops_data
