# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Openstack, LLC
# Copyright 2012 Nebula, Inc.
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
from django.core.urlresolvers import reverse_lazy
from django.core.urlresolvers import reverse

from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import views

from vsm_dashboard.api import vsm as vsmapi
from .tables import ListOpenstackIPTable
from .forms import AddOpenstackIPForm
from .forms import UpdateOpenstackIPForm
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = ListOpenstackIPTable
    template_name = 'vsm/openstackconnect/index.html'

    def get_data(self):
        _appnode_list = []
        try:
            _appnode_list = vsmapi.appnode_list(self.request)
        except:
            exceptions.handle(self.request,
                   _('Unable to retrieve openstack ip list. '))

        appnode_list = []
        for _appnode in _appnode_list:
            appnode = {"id": str(_appnode.id),
                    "ip": _appnode.ip,
                    "ssh_status": _appnode.ssh_status,
                    "log_info": _appnode.log_info}
            appnode_list.append(appnode)

        return appnode_list

class CreateView(forms.ModalFormView):
    form_class = AddOpenstackIPForm
    template_name = 'vsm/flocking/openstackconnect.html'
    success_url = reverse_lazy('horizon:vsm:openstackconnect:index')

class UpdateView(forms.ModalFormView):
    form_class = UpdateOpenstackIPForm
    template_name = 'vsm/openstackconnect/update.html'
    success_url = reverse_lazy('horizon:vsm:openstackconnect:index')

    def get_object(self):
        LOG.error("CEPH_LOG UPDATE VIEW")
        LOG.error(self.kwargs)
        if not hasattr(self, "_object"):
            try:
                appnodes = vsmapi.appnode_list(self.request)
                LOG.error(appnodes)
                for appnode in appnodes:
                    LOG.error("appnode.id")
                    LOG.error(type(appnode.id))
                    LOG.error(type(self.kwargs['appnode_id']))
                    if str(appnode.id) == self.kwargs['appnode_id']:
                        LOG.error("CEPH_LOG GET IT")
                        self._object = appnode

            except:
                redirect = reverse("horizon:vsm:openstackconnect:index")
                exceptions.handle(self.request,
                                  _('Unable to Edit Access.'),
                                  redirect=redirect)
        return self._object

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['appnode'] = self.get_object()
        return context

    def get_initial(self):
        LOG.error("CEPH_LOG UPDATE VIEW GET INITIAL")
        LOG.error(self.kwargs)
        appnode = self.get_object()
        return {'id': appnode.id,
                'ip': appnode.ip}

