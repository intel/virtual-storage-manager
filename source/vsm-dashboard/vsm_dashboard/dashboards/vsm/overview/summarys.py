
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

import logging
from vsm_dashboard.common.horizon.summary import SummaryRenderer
from vsm_dashboard.api import vsm as vsmapi
from django.utils.datastructures import SortedDict
from django.core.urlresolvers import reverse_lazy
from django.utils.safestring import mark_safe
LOG = logging.getLogger(__name__)
from vsm_dashboard.utils import get_time_delta
from vsm_dashboard.utils import get_time_delta2

class MonitorSummary(SummaryRenderer):
    verbose_name = "Monitor Summary"
    name = "monitor_summary"
    detail = {'name': "Monitor Status",
              'link': reverse_lazy("horizon:vsm:monitor-status:index")}

    def get_summary(self):
        monitor_summary = vsmapi.monitor_summary(self.request)
        LOG.error("(monitor_summary)")
        LOG.error(dir(monitor_summary))
        LOG.error("(monitor_summary)")
        data = SortedDict()
        data["Monmap Epoch"] = monitor_summary.monmap_epoch
        data["Monitors"] = monitor_summary.monitors
        data["Election epoch"] = monitor_summary.election_epoch
        data["Quorum"] = monitor_summary.quorum
        data["Last Updated"] = get_time_delta(monitor_summary.updated_at)
        return data

class OsdSummary(SummaryRenderer):
    verbose_name = "OSD Summary"
    name = "osd_summary"
    detail = {'name': "OSD Status",
              'link': reverse_lazy("horizon:vsm:osd-status:index")}

    def get_summary(self):
        osd_summary = vsmapi.osd_summary(self.request)
        LOG.error("(osd_summary)")
        LOG.error(dir(osd_summary))
        LOG.error("(osd_summary)")
        data = SortedDict()
        data["Osdmap Epoch"] = osd_summary.epoch
        data["Total OSDs"] = osd_summary.num_osds
        data["OSDs up"] = osd_summary.num_up_osds
        data["OSDs in"] = osd_summary.num_in_osds
        #data["Near Full"] = osd_summary.nearfull
        #data["Full"] = osd_summary.full
        data["Last Updated"] = get_time_delta(osd_summary.updated_at)
        return data

class MdsSummary(SummaryRenderer):
    verbose_name = "MDS Summary"
    name = "mds_summary"
    detail = {'name': "MDS Status",
              'link': reverse_lazy("horizon:vsm:mds-status:index")}

    def get_summary(self):
        mds_summary = vsmapi.mds_summary(self.request)
        LOG.error("(mds_summary)")
        LOG.error(dir(mds_summary))
        LOG.error("(mds_summary)")
        data = SortedDict()
        data["MDS Epoch"] = mds_summary.epoch
        data["Up"] = mds_summary.num_up_mdses
        data["In"] = mds_summary.num_in_mdses
        data["Max"] = mds_summary.num_max_mdses
        data["Failed"] = mds_summary.num_failed_mdses
        data["Stopped"] = mds_summary.num_stopped_mdses
        return data

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
    verbose_name = "VSM Status" + " Version: %VSM_VERSION%"
    name = "vsm_summary"

    def get_summary(self):
        vsm_summary = vsmapi.vsm_summary(self.request)
        data = SortedDict()
        data["Uptime"] = get_time_delta2(vsm_summary.created_at)
        #data["Version"] = vsm_summary.version
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
        LOG.error('<pg_summary')
        LOG.error(pg_summary)
        LOG.error('pg_summary>')
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
        LOG.error('<pg_summary')
        LOG.error(pg_summary)
        LOG.error(dir(pg_summary))
        LOG.error('pg_summary>')
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
            elif status.find('error') != -1:
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
        data['Data Capacity Used'] = str(0 if not pg_summary.data_bytes \
		else round(pg_summary.data_bytes * 1.0/1024/1024/1024, 1)) + " GB"
        data['Total Capacity Used'] = str(0 if not pg_summary.bytes_used \
		else round(pg_summary.bytes_used* 1.0/1024/1024/1024, 1)) + " GB"
        data['Capacity available'] = str(0 if not pg_summary.bytes_avail \
		else round(pg_summary.bytes_avail * 1.0/1024/1024/1024, 1)) + " GB"
        data['Capacity Total'] = str(0 if not pg_summary.bytes_total \
		else round(pg_summary.bytes_total * 1.0/1024/1024/1024, 1)) + " GB"
        return data

class ObjectSummary(SummaryRenderer):
    verbose_name = "Object Summary"
    name = "object_summary"

    def get_summary(self):
        pg_summary = vsmapi.placement_group_summary(self.request)
        data = SortedDict()
        data['Degraded objects'] = pg_summary.degraded_objects
        data['Degraded total'] = pg_summary.degraded_total
        data['Degraded ratio'] = pg_summary.degraded_ratio
        data['Unfound objects'] = pg_summary.unfound_objects
        data['Unfound total'] = pg_summary.unfound_total
        data['Unfound ratio'] = pg_summary.unfound_ratio
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

