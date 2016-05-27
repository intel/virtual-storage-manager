
# Copyright 2014 Intel Corporation, All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the"License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

import math
import logging
from vsm_dashboard.common.horizon.summary import SummaryRenderer
from vsm_dashboard.api import vsm as vsmapi
from django.utils.datastructures import SortedDict
from django.core.urlresolvers import reverse_lazy
from django.utils.safestring import mark_safe
LOG = logging.getLogger(__name__)
from vsm_dashboard.utils import get_time_delta
from vsm_dashboard.utils import get_time_delta2

def osd():
    osd_summary = vsmapi.osd_summary(None)
    osd_summary_dict = {
         "epoch":osd_summary.epoch
        ,"total":osd_summary.num_osds
        ,"up": osd_summary.num_up_osds
        ,"in": osd_summary.num_in_osds
        ,"update":get_time_delta(osd_summary.updated_at)
    }
    return osd_summary_dict

def monitor():
    monitor_summary = vsmapi.monitor_summary(None)
    monitor_summary_dict = {
         "monmap_epoch":monitor_summary.monmap_epoch
        ,"monitors":monitor_summary.monitors
        ,"election_epoch": monitor_summary.election_epoch
        ,"quorum": monitor_summary.quorum
        ,"update":get_time_delta(monitor_summary.updated_at)
    }
    return monitor_summary_dict


def mds():
    mds_summary = vsmapi.mds_summary(None)
    mds_summary_dict = {
         "epoch":mds_summary.epoch
        ,"up": mds_summary.num_up_mdses
        ,"in": mds_summary.num_in_mdses
        ,"max": mds_summary.num_max_mdses
        ,"failed":mds_summary.num_failed_mdses
        ,"stopped":mds_summary.num_stopped_mdses
    }
    return mds_summary_dict

def objects():
    pg_summary = vsmapi.placement_group_summary(None)

    pg_summary_dict = {
         "degraded_objects":pg_summary.degraded_objects
        ,"degraded_total": pg_summary.degraded_total
        ,"degraded_ratio": pg_summary.degraded_ratio
        ,"unfound_objects": pg_summary.unfound_objects
        ,"unfound_total": pg_summary.unfound_total
        ,"unfound_ratio": pg_summary.unfound_ratio
    }
    return pg_summary_dict

def performance():
    pg_summary = vsmapi.placement_group_summary(None)
  
    pg_summary_dict = {
         "read": "%s B/s" % pg_summary.read_bytes_sec
        ,"write": "%s B/s" % pg_summary.write_bytes_sec
        ,"operations":"%s operation/s" % pg_summary.op_per_sec
    }
    return pg_summary_dict 

def pg():
    pg_summary = vsmapi.placement_group_summary(None)

    #get the pag collection
    # pg_state_sort = SortedDict()
    # for pgs in pg_summary.pgs_by_state:
    #     pg_state_sort["PGs " + pgs['state_name']] = pgs['count']

    pg_summary_dict = {
         "pgmap_version":pg_summary.version
        ,"total_pgs":pg_summary.num_pgs
        #,"pg_state":pg_state_sort
        ,"update":get_time_delta(pg_summary.updated_at)
    }
    return pg_summary_dict

def format_data_size(data_size):
    """ Return a formatted string in bytes, MB, GB, or TB, not allowing any value to go over 1000.
    :param data_bytes: the integer number of bytes to be formatted.
    :return: the string formatted with a proper units suffix.
    """
    if not data_size:
        return str(0)
    if data_size > 1:
        units = [" B", " KiB", " MiB", " GiB", " TiB", " PiB", " EiB", " ZiB", " YiB"]
        idx = int(math.ceil(math.log(data_size, 1000))) - 1
        val = data_size / (math.pow(1024, idx))
        return str(round(val, 2)) + units[idx]
    return "1 B"

def capactiy():
    pg_summary = vsmapi.placement_group_summary(None)
    capactiy_summary_dict = {
         "data_used": format_data_size(pg_summary.data_bytes)
        ,"total_used": format_data_size(pg_summary.bytes_used)
        ,"available": format_data_size(pg_summary.bytes_avail)
        ,"total":  format_data_size(pg_summary.bytes_total)
    }
    return capactiy_summary_dict


class StorageGroupSummary(SummaryRenderer):
    verbose_name = "Storage Group Summary"
    name = "storage_group_summary"
    detail = {'name': "Storage Group Status",
              'link': reverse_lazy("horizon:vsm:storage-group-status:index")}

    def get_summary(self):

        _sgs = vsmapi.storage_group_status(self.request,)
        _cfg = {"storage_group_near_full_threshold":65,
            "storage_group_full_threshold":85,}
        _num = 0
        _num_near_full = 0
        _num_full = 0
        for _sg in _sgs:
            _sg.capacity_total = 1 if not _sg.capacity_total else _sg.capacity_total
            capcity_percent_used = 0 if not _sg.capacity_total else _sg.capacity_used * 100 / _sg.capacity_total
            if capcity_percent_used <_cfg["storage_group_near_full_threshold"]:
                pass
            elif capcity_percent_used < _cfg["storage_group_full_threshold"]:
                _num_near_full += 1
            else:
                _num_full += 1
            _num += 1

        data = SortedDict()
        data["Total Storage Groups"] = _num
        data["Storage Groups Near Full"] = _num_near_full
        data["Storage Groups Full"] = _num_full
        try:
            data["Last Updated"] = get_time_delta(_sgs[0].updated_at)
        except:
            pass
        return data

class VsmSummary(SummaryRenderer):
    # TODO
    #verbose_name = "VSM Status" + " Version: 2015.03-1.2"
    verbose_name = "VSM Status"
    name = "vsm_summary"

    def get_summary(self):
        vsm_summary = vsmapi.vsm_summary(self.request)
        data = SortedDict()
        data["Version"] = "2015.03-1.2"
        data["Uptime"] = get_time_delta2(vsm_summary.created_at)
        return data
        try:
            if not vsm_summary.is_ceph_active:
                data["Warning"] = mark_safe("<span style='color:red'>Cluster not responding <br> to Ceph Status</span>")
        except Exception, e:
            pass
        #data["Average Response Time"] = 123
        return data

class PGSummary(SummaryRenderer):
    # TODO
    verbose_name = "PG Summary"
    name = "pg_summary"
    detail = {'name': "PG Status",
              'link': reverse_lazy("horizon:vsm:pg-status:index")}

    def get_summary(self):
        pg_summary = vsmapi.placement_group_summary(self.request)
        LOG.info('pg_summary:%s'%pg_summary)
        #LOG.error(pg_summary)
        #LOG.error('pg_summary>')
        data = SortedDict()
        data["PGmap Version"] = pg_summary.version
        data["Total PGs"] = pg_summary.num_pgs
        for pgs in pg_summary.pgs_by_state:
            data["PGs " + pgs['state_name']] = pgs['count']
        data["Last Updated"] = get_time_delta(pg_summary.updated_at)
        return data

class PGSummaryDashboard(SummaryRenderer):
    verbose_name = "PG Summary"
    name = "pg_summary"
    detail = {'name': "PG Status",
              'link': reverse_lazy("horizon:vsm:pg-status:index")}

    def get_summary(self):
        pg_summary = vsmapi.placement_group_summary(self.request)
        #LOG.error('<pg_summary')
        #LOG.error(pg_summary)
        #LOG.error(dir(pg_summary))
        #LOG.error('pg_summary>')
        data = SortedDict()
        data["PGmap Version"] = pg_summary.version
        data["Total PGs"] = pg_summary.num_pgs
        data["PGs active+clean"] = sum([pgs['count'] for pgs in pg_summary.pgs_by_state
                                        if pgs['state_name'] == "active+clean"])
        data["PGs not active+clean"] = sum([pgs['count'] for pgs in pg_summary.pgs_by_state
                                        if pgs['state_name'] != "active+clean"])
        data["Last Updated"] = get_time_delta(pg_summary.updated_at)
        return data

class ClusterSummary(SummaryRenderer):
    # TODO
    verbose_name = "Cluster Summary"
    name = "cluster_summary"
    font = '<span id="%s"> %s </span>'
    css_id = 'health_ok'

    def get_summary(self):
        cluster_summary = vsmapi.cluster_summary(self.request)
        cluster_name = vsmapi.get_cluster_list(self.request)[1]['clusters'][0]['name']
        data = SortedDict()
        data["Cluster Name"] = cluster_name
        try:
            data["Status"] = cluster_summary.health_list[0]
            status = data['Status'].lower()
            if status.find('ok') != -1:
                self.css_id = "health_ok"
            elif status.find('war') != -1:
                self.css_id = "health_warning"
            elif status.find('err') != -1:
                self.css_id = "health_error"

            msg = self.font % (self.css_id, data["Status"])
            data["Status"] = mark_safe(msg)
        except:
            pass
        return data

class WarningSummary(SummaryRenderer):
    # TODO
    verbose_name = "Warning and Errors"
    name = "waring_summary"

    def get_summary(self):
        cluster_summary = vsmapi.cluster_summary(self.request)
        data = SortedDict()
        for k, d in enumerate(cluster_summary.detail):
            data[mark_safe("<lable id=detail-%s>Warn</lable>" % k)] = d
        for k, d in enumerate(cluster_summary.status):
            try:
                data[mark_safe("<lable id=summary-%s>%s</lable>" % (k, d.get('severity')))] = d.get('summary')
            except:
                pass
        return data

class CapacitySummary(SummaryRenderer):
    verbose_name = "Capacity Summary"
    name = "capacity_summary"

    def get_summary(self):
        pg_summary = vsmapi.placement_group_summary(self.request)
        data = SortedDict()
        data['Data Capacity Used'] = format_data_size(pg_summary.data_bytes)
        data['Total Capacity Used'] = format_data_size(pg_summary.bytes_used)
        data['Capacity available'] = format_data_size(pg_summary.bytes_avail)
        data['Capacity Total'] = format_data_size(pg_summary.bytes_total)
        return data

class PerformanceSummary(SummaryRenderer):
    verbose_name = "Performance Summary"
    name = "performance_summary"

    def get_summary(self):
        pg_summary = vsmapi.placement_group_summary(self.request)
        data = SortedDict()
        data['Total Reads'] = "%s B/s" % pg_summary.read_bytes_sec
        data['Total Writes'] = "%s B/s" % pg_summary.write_bytes_sec
        data['Total Operations'] = "%s operation/s" % pg_summary.op_per_sec
        return data

class ClusterHealthSummary(SummaryRenderer):
    # TODO
    verbose_name = "Cluster Health Summary"
    name = "cluster_health_summary"

    def get_summary_list(self):
        cluster_summary = vsmapi.cluster_summary(self.request)
        summary_list = []
        for d in cluster_summary.health_list[1:]:
            summary_list.append(d)
        return summary_list

