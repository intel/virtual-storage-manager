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
import os
import commands

from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from horizon import exceptions
from horizon import tables
from horizon import forms

from vsm_dashboard.api import vsm as vsmapi
from .tables import ListOpenstackEndpointTable
from .forms import AddOpenstackEndpointForm
from .forms import UpdateOpenstackEndpointForm

LOG = logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = ListOpenstackEndpointTable
    template_name = 'vsm/openstackconnect/index.html'

    def get_data(self):
        _appnode_list = []
        try:
            _appnode_list = vsmapi.appnode_list(self.request)
        except:
            exceptions.handle(self.request,
                   _('Unable to retrieve openstack endpoint list. '))

        appnode_list = []
        for _appnode in _appnode_list:
            appnode = {
                "id": str(_appnode.id),
                "os_tenant_name": _appnode.os_tenant_name,
                "os_username": _appnode.os_username,
                "os_password": _appnode.os_password,
                "os_auth_url": _appnode.os_auth_url,
                "os_region_name": _appnode.os_region_name,
                "ssh_user": _appnode.ssh_user,
                "ssh_status": _appnode.ssh_status,
                "log_info": _appnode.log_info
            }
            appnode_list.append(appnode)

        return appnode_list

class CreateView(forms.ModalFormView):
    form_class = AddOpenstackEndpointForm
    template_name = 'vsm/openstackconnect/create.html'

class UpdateView(forms.ModalFormView):
    form_class = UpdateOpenstackEndpointForm
    template_name = 'vsm/openstackconnect/update.html'
    success_url = reverse_lazy('horizon:vsm:openstackconnect:index')

    def get_object(self):
        LOG.info("CEPH_LOG UPDATE VIEW:%s"%self.kwargs)
        if not hasattr(self, "_object"):
            try:
                appnodes = vsmapi.appnode_list(self.request)
                for appnode in appnodes:
                    if str(appnode.id) == self.kwargs['appnode_id']:
                        self._object = appnode

            except:
                redirect = reverse("horizon:vsm:openstackconnect:index")
                exceptions.handle(self.request,
                                  _('Unable to Edit OpenStack Access.'),
                                  redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['appnode'] = self.get_object()
        return context

    def get_initial(self):
        LOG.info("CEPH_LOG UPDATE VIEW GET INITIAL: %s" % self.kwargs)
        appnode = self.get_object()
        return {
            'id': appnode.id,
            'os_tenant_name': appnode.os_tenant_name,
            'os_username': appnode.os_username,
            'os_password': appnode.os_password,
            'os_auth_url': appnode.os_auth_url,
            'os_region_name': appnode.os_region_name,
            "ssh_user": appnode.ssh_user
        }

def create_action(request):
    data = json.loads(request.body)
    # TODO deliver a cluster id in data
    data['cluster_id'] = 1
    try:
        LOG.info("CEPH_LOG in ADD OpenStack Endpoint, %s" % str(data))
        os_tenant_name = data['os_tenant_name']
        os_username = data['os_username']
        os_password = data['os_password']
        os_auth_url = data['os_auth_url']
        os_region_name = data['os_region_name']
        ssh_user = data['ssh_user']

        body = {
            'appnodes': {
                'os_tenant_name': os_tenant_name,
                'os_username': os_username,
                'os_password': os_password,
                'os_auth_url': os_auth_url,
                'os_region_name': os_region_name,
                'ssh_user': ssh_user
            }
        }
        LOG.info("CEPH_LOG in handle body %s" % str(body))
        vsmapi.add_appnodes(request, body['appnodes'])
        status = "info"
        msg = "Create Openstack Access Successfully!"
    except:
        status = "error"
        msg = "Create Openstack Access Failed! Please check crudini command and mutual trust"

    resp = dict(message=msg, status=status)
    resp = json.dumps(resp)
    return HttpResponse(resp)


def update_action(request):
    data = json.loads(request.body)
    try:
        id = data.pop('id')
        os_tenant_name = data.pop('os_tenant_name')
        os_username = data.pop('os_username')
        os_password = data.pop('os_password')
        os_auth_url = data.pop('os_auth_url')
        os_region_name = data.pop('os_region_name')
        ssh_user = data.pop('ssh_user')
        vsmapi.update_appnode(
            request, id,
            os_tenant_name=os_tenant_name,
            os_username=os_username,
            os_password=os_password,
            os_auth_url=os_auth_url,
            os_region_name=os_region_name,
            ssh_user=ssh_user,
            ssh_status="",
            log_info=""
        )
        status = "OK"
        msg = "Update Openstack Access Successfully!"
    except:
        status = "Failed"
        msg = "Update Openstack Access Failed!"

    resp = dict(message=msg, status=status)
    resp = json.dumps(resp)
    return HttpResponse(resp)
