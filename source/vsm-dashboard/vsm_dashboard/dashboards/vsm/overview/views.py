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
import logging,summarys,json,commands,time
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render
from vsm_dashboard.api import vsm as vsmapi
from vsm_dashboard.utils import get_time_delta

LOG = logging.getLogger(__name__)

def index(request):
    pool_status = vsmapi.pool_status(None)
    server_list = vsmapi.get_server_list(None)
    status = [server.status for server in server_list]
    if len(pool_status) != 0 or 'Active' in status:
        return render(request,'vsm/overview/index.html',{})
    else:
        return HttpResponseRedirect("/dashboard/vsm/clustermgmt/")

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
    if request.body:
        return HttpResponse(get_performance_IOPs(request))

def latency(request):
    # data = json.loads(request.body)
    # timestamp = int(data["timestamp"])
    if request.body:
        return HttpResponse(get_performance_Latency(request))

def bandwidth(request):
    # data = json.loads(request.body)
    # timestamp = int(data["timestamp"])
    if request.body:
        return HttpResponse(get_performance_Bandwith(request))


def CPU(request):
    if request.body:
        return HttpResponse(get_performance_cpu(request))

def perf_enabled(request):
    return HttpResponse(get_performance_enabled(request))

def get_vsm_version():
    try:
        (status, out) = commands.getstatusoutput('vsm --version')
    except:
        out = '2.0'
    return out

#get the vsm_version
def get_version():
    ceph_version = ''
    up_time = ''
    try:
        vsm_summary = vsmapi.vsm_summary(None)
        if vsm_summary is not None:
            up_time = get_time_delta(vsm_summary.created_at)
            ceph_version = vsm_summary.ceph_version
    except:
        pass
    vsm_version = get_vsm_version()
    vsm_version = {"version": vsm_version,
                   "update": up_time,
                   "ceph_version":ceph_version,
    }
    version_data = json.dumps(vsm_version)
    return version_data

#get the cluster data
def get_cluster():
    cluster_summary = vsmapi.cluster_summary(None)
    cluster_name = vsmapi.get_cluster_list(None)[1]['clusters'][0]['name']
    #HEALTH_OK HEALTH_WARN  HEALTH_ERR
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
    capactiy_used = pg_summary.bytes_used
    capactiy_total = pg_summary.bytes_total
    used_percent = ('%.2f'%((pg_summary.bytes_used/pg_summary.bytes_total)*100));
    capacity_dict = {"used":capactiy_used,"total":capactiy_total,"percent":used_percent}
    capacitydata = json.dumps(capacity_dict)
    return capacitydata

#get the OSD data
def get_OSD():
    #get the full or near full threshold
    settings = vsmapi.get_setting_dict(None)
    disk_near_full_threshold = int(settings['disk_near_full_threshold'])
    disk_full_threshold = int(settings['disk_full_threshold'])

    in_up = 0
    in_down = 0
    out_up = 0
    out_down = 0
    available_count = 0
    near_full_count = 0
    full_count = 0
    osd_summary = vsmapi.osd_summary(None)
    _osd_status = vsmapi.osd_status(None)

    for _osd in _osd_status:
        _osd_capacity_avaliable = 0 if not _osd.device['avail_capacity_kb']\
            else int(_osd.device['avail_capacity_kb']/1024)
        _osd_capacity_used = 0 if not _osd.device['used_capacity_kb']\
            else int(_osd.device['used_capacity_kb']/1024)
        _osd_capacity_total = 0 if not _osd.device['total_capacity_kb']\
            else int(_osd.device['total_capacity_kb']/1024)

        if _osd_capacity_total and _osd.state in ["In-Up", "In-Down", "Out-Up", "Out-Down", "Out-Down-Autoout"]:
            _osd_capacity_status = round(_osd_capacity_used * 1.0 / _osd_capacity_total * 100, 2)
            if _osd_capacity_status >= disk_full_threshold:
                full_count = full_count + 1
            elif _osd_capacity_status >= disk_near_full_threshold:
                near_full_count = near_full_count + 1
            else:
                available_count = available_count + 1

        if _osd.state == "In-Up":
            in_up=in_up+1
        elif _osd.state == "In-Down":
            in_down=in_down+1
        elif _osd.state == "Out-Up":
            out_up=out_up+1
        elif _osd.state == "Out-Down" or _osd.state == "Out-Down-Autoout":
            out_down=out_down+1

    OSD_dict = {"epoch":osd_summary.epoch
              ,"update":get_time_delta(osd_summary.updated_at)
              ,"in_up":in_up
              ,"in_down":in_down
              ,"out_up":out_up
              ,"out_down":out_down
              ,"capacity_full_count":full_count
              ,"capacity_near_full_count":near_full_count
              ,"capacity_available_count":available_count
              }
    OSDdata = json.dumps(OSD_dict)
    return OSDdata

#get the monitor data
def get_monitor():
    monitor_summary = vsmapi.monitor_summary(None)
    epoch = monitor_summary.monmap_epoch
    update = get_time_delta(monitor_summary.updated_at)
    quorumlist = monitor_summary.quorum.split(" ")
    quorum_leader_rank = monitor_summary.quorum_leader_rank
    leader_list_index = quorumlist.index(quorum_leader_rank)
    #monitors = monitor_summary.monitors
    Monitor_dict = {"epoch":epoch
              ,"update":update
              ,"quorum":quorumlist
              ,"selMonitor":leader_list_index}
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
    #get the threshold for storage group
    settings = vsmapi.get_setting_dict(None)
    _sgs = vsmapi.storage_group_status(None)

    _num = 0
    _num_normal = 0
    _num_near_full = 0
    _num_full = 0
    for _sg in _sgs:
        _sg.capacity_total = 1 if not _sg.capacity_total else _sg.capacity_total
        capcity_percent_used = 0 if not _sg.capacity_total else _sg.capacity_used * 100 / _sg.capacity_total
        if capcity_percent_used > float(settings["storage_group_full_threshold"]):
             _num_full+=1
        elif capcity_percent_used > float(settings["storage_group_near_full_threshold"]):
            _num_near_full+=1
        else:
            _num_normal+=1
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

def get_performance_IOPs(request):
    data = json.loads(request.body)
    start_time = data["timestamp"] and int(data["timestamp"]) or int(time.time())-30
    end_time = None

    ops_opts = {
         "metrics_name": "iops",
         "timestamp_start": start_time,
         "timestamp_end": end_time,
         "correct_cnt": None,
    }

    #print 'test1111'
    iops_data = vsmapi.get_metrics_all_types(request,ops_opts)
    #print 'test222'
    ops_r_data = iops_data.get('osd_op_r',[])
    ops_w_data = iops_data.get('osd_op_w',[])
    ops_rw_data = iops_data.get('osd_op_rw',[])


    items = {}
    for r_metric in ops_r_data:
        items[r_metric["timestamp"]] = {"timestamp": r_metric["timestamp"], "r_value": r_metric["metrics_value"] or 0, "w_value": 0, "rw_value": 0}
    for w_metric in ops_w_data:
        if items.has_key(w_metric["timestamp"]):
            items[w_metric["timestamp"]]["w_value"] = w_metric["metrics_value"] or 0
    for rw_metric in ops_rw_data:
        if items.has_key(rw_metric["timestamp"]):
            items[rw_metric["timestamp"]]["rw_value"] = rw_metric["metrics_value"] or 0

    keys = items.keys()
    keys.sort()
    metric_list = [items[key] for key in keys]

    ops_data_dict = {"metrics": metric_list}
    ops_data = json.dumps(ops_data_dict)
    return ops_data

def get_performance_Latency(request):
    data = json.loads(request.body)
    start_time = data["timestamp"] and int(data["timestamp"]) or int(time.time())-30
    end_time = None
    latency_opts = {
         "metrics_name": "lantency",
         "timestamp_start": start_time,
         "timestamp_end": end_time,
         "correct_cnt": None,
    }
    lantency_data = vsmapi.get_metrics_all_types(request,latency_opts)
    latency_r_data = lantency_data.get('osd_op_r_latency',[])
    latency_w_data = lantency_data.get('osd_op_w_latency',[])
    latency_rw_data = lantency_data.get('osd_op_rw_latency',[])


    items = {}
    for r_metric in latency_r_data:
        items[r_metric["timestamp"]] = {"timestamp": r_metric["timestamp"], "r_value":  r_metric["metrics_value"] and round( r_metric["metrics_value"],2) or 0, "w_value": 0, "rw_value": 0}
    for w_metric in latency_w_data:
        if items.has_key(w_metric["timestamp"]):
            items[w_metric["timestamp"]]["w_value"] = w_metric["metrics_value"] and  round(w_metric["metrics_value"],2) or 0
    for rw_metric in latency_rw_data:
        if items.has_key(rw_metric["timestamp"]):
            items[rw_metric["timestamp"]]["rw_value"] = rw_metric["metrics_value"] and round(rw_metric["metrics_value"],2) or 0

    keys = items.keys()
    keys.sort()
    metric_list = [items[key] for key in keys]
    ops_data_dict = {"metrics": metric_list}
    ops_data = json.dumps(ops_data_dict)
    return ops_data


def get_performance_Bandwith(request):
    data = json.loads(request.body)
    start_time = data["timestamp"] and int(data["timestamp"]) or int(time.time())-30
    end_time = None
    bandwidth_opts = {
         "metrics_name":"bandwidth"
        ,"timestamp_start":start_time
        ,"timestamp_end":end_time
        ,"correct_cnt":None
    }

    bandwidth_data = vsmapi.get_metrics_all_types(request,bandwidth_opts)
    bandwidth_in_data = bandwidth_data.get('osd_op_in_bytes',[])
    bandwidth_out_data = bandwidth_data.get('osd_op_out_bytes',[])
    items = {}
    for in_metric in bandwidth_in_data:
        items[in_metric["timestamp"]] = {"timestamp": in_metric["timestamp"], "in_value": in_metric["metrics_value"] and round(in_metric["metrics_value"],2) or 0, "out_value": 0}
    for out_metric in bandwidth_out_data:
        if items.has_key(out_metric["timestamp"]):
            items[out_metric["timestamp"]]["out_value"] = out_metric["metrics_value"] and round(out_metric["metrics_value"],2) or 0

    keys = items.keys()
    keys.sort()
    metric_list = [items[key] for key in keys]
    ops_data_dict = {"metrics": metric_list}
    ops_data = json.dumps(ops_data_dict)
    return ops_data


def get_performance_cpu(request):
    #data = json.loads(request.body)
    start_time = int(time.time())-600
    end_time = None
    cpu_opts = {
         "metrics_name":"cpu_usage"
        ,"timestamp_start":start_time
        ,"timestamp_end":end_time
    }

    cpu_data = vsmapi.get_metrics(request,cpu_opts)["metrics"]

    cpu_data_dict = {"time":[],"cpus":[]}
    cpu_data_dict['time'] = list(set([i['timestamp'] for i in cpu_data]))
    cpu_data_dict['time'].sort()
    cpu_data_dict['time'] = cpu_data_dict['time'][-7:]
    _cpu = {}
    for _metric in cpu_data:
        if not _cpu.has_key(_metric['host']):
            _cpu[_metric['host']] = []
        _cpu[_metric['host']].append('%s_%s'%(_metric['timestamp'],_metric['metrics_value']))

    keys = _cpu.keys()
    keys.sort()
    for host_name in keys:
        data_sort = list(set(_cpu[host_name]))
        data_sort.sort()
        data_sort_split = [a.split("_")[1] for a in data_sort][-7:]
        cpu_data_dict['cpus'].append({'name':host_name,'data':data_sort_split})
    cpu_data_json = json.dumps(cpu_data_dict)
    return cpu_data_json

def get_performance_enabled(request):
    settings = vsmapi.get_settings(request)
    perf_settings = [setting for setting in settings if setting.name in ('ceph_diamond_collect_interval', 'cpu_diamond_collect_interval')]
    enabled = any(setting.value != '0' for setting in perf_settings)
    perf_enabled = { "enabled": enabled }
    perf_enabled_data = json.dumps(perf_enabled)
    return perf_enabled_data
