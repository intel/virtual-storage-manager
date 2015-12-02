
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
from .views import get_crushmap_series
from .views import create_storage_group
from .views import update_storage_group

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^get_crushmap/$', get_crushmap_series, name='get_crushmap'),
    url(r'^create/$', create_storage_group, name='create'),
    url(r'^update/$', update_storage_group, name='update'),
)