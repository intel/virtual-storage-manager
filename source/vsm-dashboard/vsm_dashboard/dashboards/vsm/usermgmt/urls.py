
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
from .views import CreateView
from .views import UpdateView
from .views import update_pwd
from .views import create_user

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^update/(?P<user_id>[^/]+)/$', UpdateView.as_view(), name='update'),
    url(r'^create/$', CreateView.as_view(), name='create'),
    url(r'^update_pwd/$', update_pwd, name='update_pwd'),
    url(r'^create_user/$', create_user, name='create_user')
)
