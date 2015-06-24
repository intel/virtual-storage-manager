# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Corporation, All Rights Reserved.
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
URL patterns for the VSM Dashboard.
"""

from django.conf.urls import patterns, url, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import horizon
from django.views.generic import RedirectView

urlpatterns = patterns('',
    #url(r'^$', 'vsm_dashboard.views.splash', name='splash'),
    url(r'^$', RedirectView.as_view(url='/dashboard/vsm/')),
    url(r'^auth/', include('openstack_auth.urls')),
    url(r'^license_accept/', 'vsm_dashboard.views.license_accept',
        name='license_accept'),
    url(r'^license_cancel/', 'vsm_dashboard.views.license_cancel',
        name='license_cancel'),
    url(r'^home/', RedirectView.as_view(url='/dashboard/vsm/')),
    url(r'', include(horizon.urls))
)

# Development static app and project media serving using the staticfiles app.
urlpatterns += staticfiles_urlpatterns()

# Convenience function for serving user-uploaded media during
# development. Only active if DEBUG==True and the URL prefix is a local
# path. Production media should NOT be served by Django.
#urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^500/$', 'django.views.defaults.server_error')
    )
