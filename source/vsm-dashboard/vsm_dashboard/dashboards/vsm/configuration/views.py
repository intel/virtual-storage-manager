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

import logging
import json

from django.http import HttpResponse
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse, reverse_lazy
from horizon import forms
from vsm_dashboard.api import vsm as vsmapi
from .forms import CreateConfigurationForm
from .forms import UpdateConfigurationForm

LOG = logging.getLogger(__name__)

class IndexView(TemplateView):
    template_name = 'vsm/configuration/index.html'
    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        ceph_config = [
            {"section": "global", "items": [
                {"id": 1, "name": "name1", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name1"},
                {"id": 2, "name": "name2", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name2"},
                {"id": 3, "name": "name3", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name3"}
            ]},
            {"section": "mon", "items": [
                {"id": 4, "name": "name4", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name4"},
                {"id": 5, "name": "name5", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name5"},
                {"id": 6, "name": "name6", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name6"},
                {"id": 7, "name": "name7", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name7"}
            ]},
            {"section": "osd", "items": [
                {"id": 8, "name": "name8", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name8"},
                {"id": 9, "name": "name9", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name9"}
            ]},
            {"section": "mds", "items": [
                {"id": 10, "name": "name10", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name10"},
                {"id": 11, "name": "name11", "value": "1", "default_value": "1", "category": "CEPH", "alterable": True, "description": "name11"}
            ]}
        ]
        context["config_list"] = ceph_config
        return context;


class CreateView(forms.ModalFormView):
    form_class = CreateConfigurationForm
    template_name = 'vsm/configuration/create.html'
    success_url = reverse_lazy('horizon:vsm:configuration:index')

class UpdateView(forms.ModalFormView):
    form_class = UpdateConfigurationForm
    template_name = 'vsm/configuration/update.html'
    success_url = reverse_lazy('horizon:vsm:configuration:index')

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['config_id'] = self.kwargs['config_id']
        return context

    def get_initial(self):
        #TODO: you can use this argument to get the configuration entity to update.
        config_id = self.kwargs['config_id']
        return {'name': "12345",
                'section': "mon",
                'default_value': "hahaha",
                'current_value': "hehehehe"}


def create(request):
    data = json.loads(request.body)
    print "============create the configuration============="
    print data
    try:
        #TODO: create the configuration
        resp = dict(message="Create configuration successfully", status="OK", data="")
        resp = json.dumps(resp)
        return HttpResponse(resp)
    except:
        resp = dict(message="Create configuration failed", status="Failed", data="")
        resp = json.dumps(resp)
        return HttpResponse(resp)


def update(request):
    data = json.loads(request.body)
    print "============update the configuration============="
    print data
    try:
        #TODO: create the configuration
        resp = dict(message="Update configuration successfully", status="OK", data="")
        resp = json.dumps(resp)
        return HttpResponse(resp)
    except:
        resp = dict(message="Update configuration failed", status="Failed", data="")
        resp = json.dumps(resp)
        return HttpResponse(resp)


def delete_action(request):
    data = json.loads(request.body)
    print "============delete the configuration============="
    print data
    try:
        #TODO: create the configuration
        resp = dict(message="Delete configuration successfully", status="OK", data="")
        resp = json.dumps(resp)
        return HttpResponse(resp)
    except:
        resp = dict(message="Delete configuration failed", status="Failed", data="")
        resp = json.dumps(resp)
        return HttpResponse(resp)


