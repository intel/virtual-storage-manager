
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
from .views import IndexView
from .views import version,status,capacity,OSD,monitor,MDS,storage,IOPS,PG

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^version/$', version, name='version'),
    url(r'^status/$', status, name='status'),
    url(r'^capcity/$', capacity, name='capcity'),
    url(r'^osd/$', OSD, name='OSD'),
    url(r'^monitor/$', monitor, name='monitor'),
    url(r'^mds/$', MDS, name='MDS'),
    url(r'^storage/$', storage, name='storage'),
    url(r'^IOPS/$', IOPS, name='IOPS'),
    url(r'^PG/$', PG, name='PG'),
)