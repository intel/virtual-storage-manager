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
import os
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import views

from vsm_dashboard import api
from .utils import get_admin_tenant

from .tables import ListUserTable
from .forms import CreateUserForm
from .forms import UpdateUserForm
from django.http import HttpResponse
from django import http

import json
LOG = logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = ListUserTable
    template_name = 'vsm/usermgmt/index.html'

    def get_data(self):

        admin_tenant = get_admin_tenant(self.request)
        _user_list = api.keystone.user_list(self.request, admin_tenant.id)
        LOG.info("USER LIST")
        #LOG.error(dir(self.request.user))
        #LOG.error(self.request.user.roles)
        #LOG.error(api.keystone.role_list(self.request))
        if self.request.user.username != "admin":
            _user_list = [x for x in _user_list if x.id == self.request.user.id]

        user_list = []
        for _user in _user_list:
            user = {"id": _user.id,
                    "email": _user.email,
                    "enabled": _user.enabled,
                    "name": _user.name,}
            user_list.append(user)
        LOG.info("CEPH_LOG user list: %s" % user_list)

        return user_list

class CreateView(forms.ModalFormView):
    form_class = CreateUserForm
    template_name = 'vsm/usermgmt/create.html'
    success_url = reverse_lazy('horizon:vsm:usermgmt:index')

class UpdateView(forms.ModalFormView):
    form_class = UpdateUserForm
    template_name = 'vsm/usermgmt/update.html'
    success_url = reverse_lazy('horizon:vsm:usermgmt:index')

    @method_decorator(sensitive_post_parameters('password',
                                                'confirm_password'))
    def dispatch(self, *args, **kwargs):
        return super(UpdateView, self).dispatch(*args, **kwargs)

    def get_object(self):
        if not hasattr(self, "_object"):
            try:
                self._object = api.keystone.user_get(self.request,
                                                     self.kwargs['user_id'],
                                                     admin=True)
            except:
                redirect = reverse("horizon:vsm:usermgmt:index")
                exceptions.handle(self.request,
                                  _('Unable to update user.'),
                                  redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['user'] = self.get_object()
        return context

    def get_initial(self):
        user = self.get_object()
        return {'id': user.id,
                'name': user.name,
                'tenant_id': getattr(user, 'tenantId', None),
                'email': user.email}

    def form_valid(self, form):
        try:
            handled = form.handle(self.request, form.cleaned_data)
        except Exception:
            handled = None
            exceptions.handle(self.request)

        if handled:
            if "HTTP_X_HORIZON_ADD_TO_FIELD" in self.request.META:
                field_id = self.request.META["HTTP_X_HORIZON_ADD_TO_FIELD"]
                data = [self.get_object_id(handled),
                        self.get_object_display(handled)]
                response = http.HttpResponse(json.dumps(data))
                response["X-Horizon-Add-To-Field"] = field_id
            elif isinstance(handled, http.HttpResponse):
                return handled
            else:
                success_url = self.get_success_url()
                response = http.HttpResponseRedirect(success_url)
                # TODO(gabriel): This is not a long-term solution to how
                # AJAX should be handled, but it's an expedient solution
                # until the blueprint for AJAX handling is architected
                # and implemented.
                response['X-Horizon-Location'] = success_url
            return response
        else:
            # If handled didn't return, we can assume something went
            # wrong, and we should send back the form as-is.
            return self.form_invalid(form)



def create_user(request):
    data = json.loads(request.body)
    print "============create user================="
    print data

    try:
        admin_tenant = get_admin_tenant(request)
        tenant_id = admin_tenant.id
        #create user
        ret = api.keystone.user_create(request, data['name'], data['email'],
                                            data['pwd'], tenant_id, enabled=True)
        #assign the role
        roles = api.keystone.role_list(request)
        for role in roles:
            if role.name in ['admin', 'KeystoneAdmin']:
                api.keystone.add_tenant_user_role(request, tenant_id, ret.id, role.id)
        
        resp = dict(message="Create user successfully", status="OK", data="")
        resp = json.dumps(resp)
        return HttpResponse(resp)
    except:
        resp = dict(message="Create User failed", status="Bad", data="")
        resp = json.dumps(resp)
        return HttpResponse(resp)


def update_pwd(request):
    data = json.loads(request.body)
    print "=============update pwd================"
    print data

    api.keystone.user_update_password(request, data["id"], data["pwd"])
    resp = dict(message="Update User", status="OK", data="")
    resp = json.dumps(resp)
    return HttpResponse(resp)





