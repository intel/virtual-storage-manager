
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
from .views import IndexView,remove_ec_profiles,add_ec_profile,add_ec_profile_view
urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^add_ec_profile_view/$', add_ec_profile_view, name='add_ec_profile_view'),
    url(r'^add_ec_profile/$', add_ec_profile, name='add_ec_profile'),
    url(r'^remove_ec_profiles/$', remove_ec_profiles, name='remove_ec_profiles'),
)

