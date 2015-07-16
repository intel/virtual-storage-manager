
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
from .views import DevicesAction
from .views import AddOSDView,get_osd_list,add_new_osd_action,check_device_path
urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^add_new_osd/$', AddOSDView.as_view(), name='add_new_osd'),
    url(r'^get_osd_list/$', get_osd_list, name='get_osd_list'),
    url(r'^add_new_osd_action/$', add_new_osd_action, name='add_new_osd_action'),
    url(r'^check_device_path/$', check_device_path, name='check_device_path'),
    url(r'^devices/(?P<action>\w+)$', DevicesAction, name='devicesaction'),
    url(r'/', IndexView.as_view(), name='index'),
)

