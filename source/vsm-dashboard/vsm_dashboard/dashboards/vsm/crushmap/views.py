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

from __future__ import division
import logging
import json
from django.views.generic import TemplateView
from django.http import HttpResponse
from vsm_dashboard.api import vsm as vsmapi
from horizon import exceptions

LOG = logging.getLogger(__name__)

class ModalCrushMapMixin(object):

    def get_context_data(self, **kwargs):
        context = super(ModalCrushMapMixin, self).get_context_data(**kwargs)
        context["sg_list"] = get_sg_list()
        return context

class IndexView(ModalCrushMapMixin, TemplateView):
    template_name = 'vsm/crushmap/index.html'


def get_crushmap_series(request):
    body = {'cluster_id':1}
    ret_code,node_list = vsmapi.get_crushmap_tree_data(request,body)
    node_list = node_list['tree_node']
    print 'node_list=======',node_list

    #generate the crushmap nodes
    crushmap_nodes = []
    type_list = []
    for node in node_list:
        is_parent = False
        is_open = False
        font = ""

        #get the type list
        is_type_exist = False
        for type_item in type_list:
            if type_item["id"] == node["type"]:
                is_type_exist = True
                break
        if is_type_exist == False:
            type_list.append({
                "id":node["type"],
                "name":node["type_name"],
            })

        #if parent id is none,it's "root"
        pID_list = node.get("parent_id",["root"])
        print '111===',node
        for pID in pID_list:
            if pID == "root":
                is_parent = True
                is_open = True
                pID = "root"
            item = {
                "id":node["id"],
                "pId":pID,
                "type_id":node["type"],
                "type_name":node["type_name"],
                "name":node["name"],
                "font":"",
                "open":is_open,
                "isParent":is_parent,
            }
            #append the item into crushmap
            crushmap_nodes.append(item)
    #sort the type_list
    type_list.sort(key=lambda x:x["id"])
    resp = dict(message="", status="OK",crushmap=crushmap_nodes,type_list=type_list)
    resp = json.dumps(resp)
    return HttpResponse(resp)

def get_sg_list():
    _sgs = []
    try:
        _sgs = vsmapi.storage_group_status(None,)
        if _sgs:
            logging.debug("resp body in view: %s" % _sgs)
    except:
        exceptions.handle(None,'Unable to retrieve storage group list.')
    return _sgs


def create_storage_group(request):
    body = json.loads(request.body)
    try:
        http_response_code,ret = vsmapi.storage_group_create_with_takes(request, body=body)
        print '---ret====',ret
        if len(ret.get('error_code')) > 0:
            status = "Failed"
            msg = ret.get('error_msg')
        else:
            status = "OK"
            msg = ret.get('info')
    except ex:
        print ex
        status = "Failed"
        msg = "Add Storage Group Failed!Unknown exception!"

    resp = dict(message=msg, status=status)
    resp = json.dumps(resp)
    return HttpResponse(resp)


def update_storage_group(request):
    body = json.loads(request.body)
    try:
        http_response_code,ret = vsmapi.storage_group_update_with_takes(request, body=body)
        print '---ret====',ret
        if len(ret.get('error_code')) > 0:
            status = "Failed"
            msg = ret.get('error_msg')
        else:
            status = "OK"
            msg = ret.get('info')
    except ex:
        print ex
        status = "Failed"
        msg = "Update Stroage Group Failed!Unknown exception!"

    resp = dict(message=msg, status=status)
    resp = json.dumps(resp)
    return HttpResponse(resp)
