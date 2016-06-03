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

import os
import json
import logging

from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from vsm_dashboard.api import vsm as vsmapi
from .form import CreatePool
from .tables import ListPoolTable
from .tables import ListPresentPoolTable
from .utils import list_cinder_service
from .utils import from_keystone_v2
from .utils import from_keystone_v3

LOG = logging.getLogger(__name__)


class ModalEditTableMixin(object):
    def get_template_names(self):
        if self.request.is_ajax():
            if not hasattr(self, "ajax_template_name"):
                # Transform standard template name to ajax name (leading "_")
                bits = list(os.path.split(self.template_name))
                bits[1] = "".join(("_", bits[1]))
                self.ajax_template_name = os.path.join(*bits)
            template = self.ajax_template_name
        else:
            template = self.template_name
        return template

    def get_context_data(self, **kwargs):
        context = super(ModalEditTableMixin, self).get_context_data(**kwargs)
        context['verbose_name'] = getattr(self, "verbose_name", "")
        context['submit_btn'] = getattr(self, "submit_btn", {})
        if self.request.is_ajax():
            context['hide'] = True
        return context

class IndexView(tables.DataTableView):
    table_class = ListPoolTable
    template_name = 'vsm/rbdpools/index.html'

    def get_data(self):
        pools = []
        pool_usages = []
        # TODO pools status
        try:
            pools = vsmapi.pool_list(self.request,)
            pool_usages = vsmapi.pool_usages(self.request)
            logging.debug("resp body in view: %s" % pools)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve storage pool list. '))
        pool_usage_dict = {}
        for usage in pool_usages:
            pool_usage_dict.setdefault(str(usage.pool_id), usage)

        for pool in pools:
            pool['id'] = str(pool['id'])
            if pool['id'] in pool_usage_dict:
                pool['attach_status'] = pool_usage_dict[pool['id']].attach_status
            else:
                pool['attach_status'] = "no"

        pools = [x for x in pools if x['tag'] != "SYSTEM" and not x['erasure_code_status']
                     and not str(x['cache_tier_status']).startswith("Cache pool for")]
        return pools

class PresentPoolsView(tables.DataTableView):
    table_class = ListPresentPoolTable
    template_name = 'vsm/rbdpools/rbdsaction.html'
    verbose_name = "Present Pools"

    def get_data(self):
        pools = []
        pool_usages = []
        # TODO pools status
        try:
            pools = vsmapi.pool_list(self.request,)
            pool_usages = vsmapi.pool_usages(self.request)
            logging.debug("resp body in view: %s" % pools)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve storage pool list. '))
        pool_usage_dict = {}
        for usage in pool_usages:
            pool_usage_dict.setdefault(str(usage.pool_id), usage)

        for pool in pools:
            pool['id'] = str(pool['id'])
            if pool['id'] in pool_usage_dict:
                pool['attach_status'] = pool_usage_dict[pool['id']].attach_status
            else:
                pool['attach_status'] = "no"

        pools = [x for x in pools if x['tag'] != "SYSTEM"]
        pools = [x for x in pools if x['attach_status'] == "no"]
        pools = [x for x in pools if x['tag'] != "SYSTEM" and not x['erasure_code_status']
             and not str(x['cache_tier_status']).startswith("Cache pool for")]
        return pools

class CreateView(forms.ModalFormView):
    form_class = CreatePool
    template_name = 'vsm/flocking/create.html'
    success_url = reverse_lazy('horizon:vsm:rbdpools:index')

def PoolsAction(request, action):
    data = json.loads(request.body)
    msg = ""
    status = ""
    # glance only need to present one pool
    as_glance_store_pool_num = 0
    for info in data:
        if info["as_glance_store_pool"] == True:
            as_glance_store_pool_num += 1
    if as_glance_store_pool_num > 1:
        msg = "more than one pool as glance backend"
        status = "error"
        resp = dict(message=msg, status=status, data="")
        resp = json.dumps(resp)
        return HttpResponse(resp)

    if as_glance_store_pool_num:
        pool_usages = vsmapi.pool_usages(request)
        for pool_usage in pool_usages:
            print pool_usage.as_glance_store_pool
            if pool_usage.as_glance_store_pool:
                msg = "there is one pool as glance backend now"
                status = "error"
                resp = dict(message=msg, status=status, data="")
                resp = json.dumps(resp)
                return HttpResponse(resp)

    if not len(data):
        status = "error"
        msg = "No pool selected"
    else:
        # TODO add cluster_id in data

        if action == "present":
            print data
            pools = []
            for x in data:
                cinder_volume_host = x['cinder_volume_host']
                if (cinder_volume_host == "" or cinder_volume_host == None) and \
                        (x['as_glance_store_pool'] == "" or x['as_glance_store_pool'] == None):
                    status = "error"
                    msg = "The Cinder Volume Host and As Glance Store Pool are all null"
                pools.append({'pool_id': x['id'],
                              'cinder_volume_host': cinder_volume_host,
                              'appnode_id': x['appnode_id'],
                              'as_glance_store_pool': x['as_glance_store_pool']})
            if msg == "" and status == "":
                print "========Start Present Pools==========="
                result = vsmapi.present_pool(request, pools)
                print result
                host_list = ""
                for host in result['host']:
                    host_list = host + "," + host_list
                if result['status'] == "bad":
                    status = "warning"
                    msg = "Not found crudini commmand in host: %s" % host_list
                elif result['status'] == "unreachable":
                    status = "warning"
                    msg = "Please check ssh with no password between vsm controller and host: %s" % host_list
                else:
                    status = "info"
                    msg = "Begin to Present Pools!"
                print "========End Present Pools==========="

    resp = dict(message=msg, status=status, data="")
    resp = json.dumps(resp)
    return HttpResponse(resp)


def get_openstack_region_select_data(request):
    appnodes = vsmapi.appnode_list(request)
    print "================appnodes get_openstack_region_select_data=========="
    print appnodes
    appnode_list = []
    for appnode in appnodes:
        appnode_dict = {}
        auth_host = appnode.os_auth_url.split(":")[1][2:]
        appnode_dict.update({"display": auth_host + "/" + appnode.os_region_name,
                             "id": appnode.id
                             })
        appnode_list.append(appnode_dict)

    print appnode_list
    data = tuple(appnode_list)
    return HttpResponse(json.dumps(data))


def get_select_data(request):
    print "===================================="
    data = json.loads(request.body)
    print data
    appnode_id  = data["appnode_id"]
    print appnode_id

    service_list = []
    data = {}
    if appnode_id:
        appnodes = vsmapi.appnode_list(request)
        print appnodes
        for appnode in appnodes:
            print appnode.id
            if int(appnode.id) == int(appnode_id):
                print "====================here=============="
                tenant_name = appnode.os_tenant_name
                username = appnode.os_username
                password = appnode.os_password
                auth_url = appnode.os_auth_url
                region_name = appnode.os_region_name
                try:
                    keystone_version = auth_url.strip("/").split("/")[-1]
                    if keystone_version == "v3":
                        tenant_id = tenant_name
                        token, cinder_api_host = from_keystone_v3(tenant_name,
                                                                  username,
                                                                  password,
                                                                  auth_url,
                                                                  region_name)
                    else:
                        token, tenant_id, cinder_api_host = \
                            from_keystone_v2(tenant_name, username, password,
                                             auth_url, region_name)
                    cinder_service_list = list_cinder_service(cinder_api_host, token, tenant_id)

                    cinder_volume_down_list = []
                    for cinder in cinder_service_list:
                        if cinder["state"] == "down":
                            cinder_volume_down_list.append(cinder)

                    if len(cinder_volume_down_list) == 0:
                        for cinder in cinder_service_list:
                            if cinder["binary"] == "cinder-volume":
                                service_list.append(cinder["host"])
                    else:
                        for cinder in cinder_service_list:
                            if cinder["binary"] == "cinder-volume" and \
                                            "@" in cinder["host"]:
                                host = cinder["host"].split("@")[0]
                                if host not in service_list:
                                    service_list.append(host)
                            elif cinder["binary"] == "cinder-volume" and \
                                            "@" not in cinder["host"]:
                                service_list.append(cinder["host"])
                    print service_list
                except:
                    service_list = []

        data = {"host": service_list}
        print data
    return HttpResponse(json.dumps(data))


def get_select_data2(request):
    data = ()
    return HttpResponse(json.dumps(data))
