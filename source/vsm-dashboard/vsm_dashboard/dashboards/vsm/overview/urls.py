
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

from django.conf.urls import patterns, url
from .views import index
from .views import version,cluster,capacity,OSD,monitor,MDS,storage,IOPS,PG,latency,bandwidth,CPU,perf_enabled
from .views import osd_summary,monitor_summary,mds_summary,objects_summary,performance_summary,pg_summary,capacity_summary

urlpatterns = patterns('',
    url(r'^$', index, name='index'),
    url(r'^version/$', version, name='version'),
    url(r'^cluster/$', cluster, name='cluster'),
    url(r'^capcity/$', capacity, name='capcity'),
    url(r'^osd/$', OSD, name='OSD'),
    url(r'^monitor/$', monitor, name='monitor'),
    url(r'^mds/$', MDS, name='MDS'),
    url(r'^storage/$', storage, name='storage'),
    url(r'^IOPS/$', IOPS, name='IOPS'),
    url(r'^PG/$', PG, name='PG'),
    url(r'^latency/$', latency, name='latency'),
    url(r'^bandwidth/$', bandwidth, name='bandwidth'),
    url(r'^CPU/$', CPU, name='CPU'),
    url(r'^perf_enabled/$', perf_enabled, name='perf_enabled'),

    url(r'^osd_summary/$', osd_summary, name='osd_summary'),
    url(r'^monitor_summary/$', monitor_summary, name='monitor_summary'),
    url(r'^mds_summary/$', mds_summary, name='mds_summary'),
    url(r'^objects_summary/$', objects_summary, name='objects_summary'),
    url(r'^performance_summary/$', performance_summary, name='performance_summary'),
    url(r'^pg_summary/$', pg_summary, name='pg_summary'),
    url(r'^capacity_summary/$', capacity_summary, name='capacity_summary'),
)
