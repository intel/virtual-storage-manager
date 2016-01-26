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
from django.core.urlresolvers import reverse, reverse_lazy



from horizon import forms
from vsm_dashboard.api import vsm as vsmapi
from django.http import HttpResponse
from .form import CephUpgrade

import json
LOG = logging.getLogger(__name__)



class CephUpgradeView(forms.ModalFormView):
    form_class = CephUpgrade
    template_name = 'vsm/cephupgrade/ceph_upgrade.html'
    success_url = reverse_lazy('horizon:vsm:clustermgmt:index')

def ceph_upgrade(request):
    data = json.loads(request.body)
    code,msg = vsmapi.ceph_upgrade(request, data[0])
    status = "info"
    msg = msg.get('message')

    poolusages = vsmapi.pool_usages(request)
    host_list = []
    if poolusages:
        for pool_usage in poolusages:
            volume_host = pool_usage.get("cinder_volume_host")
            if volume_host not in host_list:
                host_list.append(volume_host)
        hosts = ", ".join(host_list)
        msg = msg + "\nPlease upgrade ceph on volume hosts: %s" % hosts

    resp = dict(message=msg, status=status, data="")
    resp = json.dumps(resp)
    return HttpResponse(resp)







