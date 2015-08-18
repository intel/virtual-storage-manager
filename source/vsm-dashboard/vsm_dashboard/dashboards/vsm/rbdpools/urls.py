
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
from .views import IndexView, PresentPoolsView
from .views import PoolsAction,get_select_data,get_openstack_region_select_data,get_select_data2

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^presentpools/$', PresentPoolsView.as_view(), name='presentpoolsview'),
    url(r'^pools/(?P<action>\w+)$', PoolsAction, name='poolsaction'),
    url(r'^get_select_data/$', get_select_data, name='get_select_data'),
    url(r'^get_select_data2/$', get_select_data2, name='get_select_data2'),
    url(r'^get_openstack_region_select_data/$', get_openstack_region_select_data, name='get_openstack_region_select_data'),
    #url(r'^create/$', CreateView.as_view(), name='create'),
    )

