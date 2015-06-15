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
from django.core.urlresolvers import reverse_lazy

from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import views

from vsm_dashboard.api import vsm as vsmapi
from .tables import ListStorageGroupTable
from .forms import CreateStorageGroupForm
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = ListStorageGroupTable
    template_name = 'vsm/storage-group-management/index.html'

    def get_data(self):
        _sgs = []
        #_sgs= vsmapi.get_sg_list(self.request,)
        try:
            _sgs = vsmapi.storage_group_status(self.request,)
            if _sgs:
                logging.debug("resp body in view: %s" % _sgs)
            settings = vsmapi.get_setting_dict(self.request)
            sg_near_full_threshold = settings['storage_group_near_full_threshold']
            sg_full_threshold = settings['storage_group_full_threshold']
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve sever list. '))

        storage_group_status = _sgs
        return storage_group_status

class CreateView(forms.ModalFormView):
    form_class = CreateStorageGroupForm
    template_name = 'vsm/storage-group-management/createstoragegroup.html'
    success_url = reverse_lazy('horizon:vsm:storage-group-management:index')


def create_storage_group(request):
    status = ""
    msg = ""
    body = json.loads(request.body)
    print ""
    print "============Create Storage Group==============="
    print body
    try:
        rsp = vsm_api.storage_group_create(request, body=body)
        status = "OK"
        msg = "Add Cache Tier Successfully!"
    except ex:
        print ex
        status = "Failed"
        msg = "Add Cache Tier Failed!"

    resp = dict(message=msg, status=status)
    resp = json.dumps(resp)
    return HttpResponse(resp)