
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
from .views import add_new_osd
from .views import add_new_osd_action,check_device_path,get_smart_info,get_available_disks
from .views import restart_osd,remove_osd,restore_osd

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^add_new_osd/$', add_new_osd, name='add_new_osd'),
    url(r'^add_new_osd_action/$', add_new_osd_action, name='add_new_osd_action'),
    url(r'^check_device_path/$', check_device_path, name='check_device_path'),
    url(r'^get_available_disks/$', get_available_disks, name='get_available_disks'),
    url(r'^devices/(?P<action>\w+)$', DevicesAction, name='devicesaction'),
    url(r'^get_smart_info/$', get_smart_info, name='get_smart_info'),

    url(r'^restart_osd/$', restart_osd, name='restart_osd'),
    url(r'^remove_osd/$', remove_osd, name='remove_osd'),
    url(r'^restore_osd/$', restore_osd, name='restore_osd'),

    url(r'/', IndexView.as_view(), name='index'),
)

