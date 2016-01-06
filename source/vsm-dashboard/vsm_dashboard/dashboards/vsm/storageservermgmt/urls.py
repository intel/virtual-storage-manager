
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
from .views import ServersAction
from .views import AddServersView
from .views import AddServerDetailView
from .views import RemoveServersView
from .views import AddMonitorsView
from .views import RemoveMonitorsView
from .views import StartServersView
from .views import StopServersView
from .views import ResetStatus
from .views import update_server_list
from .views import get_server_by_name
from .views import add_server

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^addserversview/$', AddServersView.as_view(), name='addserversview'),
    url(r'^removeserversview/$', RemoveServersView.as_view(), name='removeserversview'),
    url(r'^addmonitorsview/$', AddMonitorsView.as_view(), name='addmonitorsview'),
    url(r'^removemonitorsview/$', RemoveMonitorsView.as_view(), name='removemonitorsview'),
    url(r'^startserversview/$', StartServersView.as_view(), name='startserversview'),
    url(r'^stopserversview/$', StopServersView.as_view(), name='stopserversview'),
    url(r'^servers/(?P<action>\w+)$', ServersAction, name='serversaction'),
    url(r'^reset_status/(?P<server_id>\w+)$', ResetStatus, name='reset_status'),
    url(r'^update_server_list/$', update_server_list, name='update_server_list'),

    url(r'^addserverdetailview/$', AddServerDetailView, name='addserverdetailview'),
    url(r'^get_server_by_name/$', get_server_by_name, name='get_server_by_name'),
    url(r'^add_server/$', add_server, name='add_server'),

)
