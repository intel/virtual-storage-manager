# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Corporation, All Rights Reserved.
#
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

from django import shortcuts
from django.views.decorators import vary
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context
from django.conf import settings

import horizon

from openstack_auth.views import login

from vsm_dashboard import api

def get_user_home(user):
    #if user.is_superuser:
    #    return horizon.get_dashboard('admin').get_absolute_url()
    return horizon.get_dashboard('vsm').get_absolute_url()

def license_gate(request):
    _template = get_template('license.html')
    context = Context()
    html = _template.render(context=context)
    return HttpResponse(html)

def license_accept(request):
    api.vsm.license_create(request)
    api.vsm.license_update(request, True)
	#Redirect to cluster create page if user accept license.
	#TODO(fengqian): When trun to cluster create page,
	#All other functions should be unavaliable.
    return shortcuts.redirect('/dashboard/vsm/clustermgmt')

def license_cancel(request):
    return HttpResponseRedirect(settings.LOGOUT_URL)

@vary.vary_on_cookie
def splash(request):
    if request.user.is_authenticated():
        #license_status = api.vsm.license_get(request)[1]
        #if license_status is None or\
        #    license_status.get('license_accept', False) == False:
        #        return license_gate(request)
        #else:
        return shortcuts.redirect(get_user_home(request.user))
    form = login(request)
    request.session.clear()
    request.session.set_test_cookie()
    return shortcuts.render(request, 'splash.html', {'form': form})
