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
    # node_list = [
    #     {'type': 4,'type_name': "type4", 'id': -16, 'sg':[],'name': 'vsm','nocheck':False,"take":"",'take':"take_16"},
    #
    #     {'parent_id': [-16], 'type': 3,'type_name':"type3", 'id': -13, 'sg':[],'name': 'performances','nocheck':False,'take':"take_13"},
    #     {'parent_id': [-16], 'type': 3,'type_name':"type3", 'id': -15, 'sg':[],'name': 'capacity','nocheck':False,'take':"take_15"},
    #     {'parent_id': [-16], 'type': 3,'type_name':"type3", 'id': -14, 'sg':[],'name': 'high_performance_test','nocheck':False,'take':"take_14"},
    #
    #     {'parent_id': [-14], 'type': 2,'type_name':"type2", 'id': -11, 'sg':[],'name': 'zone0_high_performance_test','nocheck':False,'take':"take_14"},
    #     {'parent_id': [-13], 'type': 2,'type_name':"type2", 'id': -10, 'sg':[],'name': 'zone0_performance','nocheck':False,'take':"take_13"},
    #     {'parent_id': [-15], 'type': 2,'type_name':"type2", 'id': -12, 'sg':[],'name': 'zone0_capacity','nocheck':False,'take':"take_15"},
    #
    #     {'parent_id': [-10], 'type': 1,'type_name':"type1", 'id': -4, 'sg':[],'name': 'ceph02_performance_zone0','nocheck':False,'take':"take_4"},
    #     {'parent_id': [-10], 'type': 1,'type_name':"type1", 'id': -7, 'sg':[],'name': 'ceph03_performance_zone0','nocheck':False,'take':"take_7"},
    #     {'parent_id': [-10], 'type': 1,'type_name':"type1", 'id': -1, 'sg':[],'name': 'ceph01_performance_zone0','nocheck':False,'take':"take_1"},
    #     {'parent_id': [-11], 'type': 1,'type_name':"type1", 'id': -8, 'sg':[],'name': 'ceph03_high_performance_test_zone0','nocheck':False,'take':"take_8"},
    #     {'parent_id': [-11], 'type': 1,'type_name':"type1", 'id': -5, 'sg':[],'name': 'ceph02_high_performance_test_zone0','nocheck':False,'take':"take_5"},
    #     {'parent_id': [-11], 'type': 1,'type_name':"type1", 'id': -2, 'sg':[],'name': 'ceph01_high_performance_test_zone0','nocheck':False,'take':"take_2"},
    #     {'parent_id': [-12], 'type': 1,'type_name':"type1", 'id': -9, 'sg':[],'name': 'ceph03_capacity_zone0','nocheck':False,'take':"take_9"},
    #     {'parent_id': [-12], 'type': 1,'type_name':"type1", 'id': -3, 'sg':[],'name': 'ceph01_capacity_zone0','nocheck':False,'take':"take_4"},
    #     {'parent_id': [-12], 'type': 1,'type_name':"type1", 'id': -6, 'sg':[],'name': 'ceph02_capacity_zone0','nocheck':False,'take':"take_6"},
    #
    #     {'parent_id': [-1], 'type': 0,'type_name':"type0", 'id': 8, 'sg':[1,2,3],'name': 'osd.8','nocheck':True,"take":""},
    #     {'parent_id': [-1], 'type': 0,'type_name':"type0", 'id': 10, 'sg':[3],'name': 'osd.10','nocheck':True,"take":""},
    #     {'parent_id': [-1], 'type': 0,'type_name':"type0", 'id': 9, 'sg':[1,2],'name': 'osd.9','nocheck':True,"take":""},
    #     {'parent_id': [-2], 'type': 0,'type_name':"type0", 'id': 0, 'sg':[2],'name': 'osd.0','nocheck':True,"take":""},
    #     {'parent_id': [-3], 'type': 0,'type_name':"type0", 'id': 2, 'sg':[2],'name': 'osd.2','nocheck':True,"take":""},
    #     {'parent_id': [-3], 'type': 0,'type_name':"type0", 'id': 4, 'sg':[1],'name': 'osd.4','nocheck':True,"take":""},
    #     {'parent_id': [-3], 'type': 0,'type_name':"type0", 'id': 6, 'sg':[1],'name': 'osd.6','nocheck':True,"take":""},
    #     {'parent_id': [-3], 'type': 0,'type_name':"type0", 'id': 1, 'sg':[1,3],'name': 'osd.1','nocheck':True,"take":""},
    #     {'parent_id': [-3], 'type': 0,'type_name':"type0", 'id': 3, 'sg':[3],'name': 'osd.3','nocheck':True,"take":""},
    #     {'parent_id': [-3], 'type': 0,'type_name':"type0", 'id': 5, 'sg':[],'name': 'osd.5','nocheck':True,"take":""},
    #     {'parent_id': [-3], 'type': 0,'type_name':"type0", 'id': 7, 'sg':[],'name': 'osd.7','nocheck':True,"take":""},
    #     {'parent_id': [-4], 'type': 0,'type_name':"type0", 'id': 19, 'sg':[],'name': 'osd.19','nocheck':True,"take":""},
    #     {'parent_id': [-4], 'type': 0,'type_name':"type0", 'id': 20, 'sg':[],'name': 'osd.20','nocheck':True,"take":""},
    #     {'parent_id': [-4], 'type': 0,'type_name':"type0", 'id': 21, 'sg':[],'name': 'osd.21','nocheck':True,"take":""},
    #     {'parent_id': [-5], 'type': 0,'type_name':"type0", 'id': 11, 'sg':[],'name': 'osd.11','nocheck':True,"take":""},
    #     {'parent_id': [-6], 'type': 0,'type_name':"type0", 'id': 13, 'sg':[],'name': 'osd.13','nocheck':True,"take":""},
    #     {'parent_id': [-6], 'type': 0,'type_name':"type0", 'id': 12, 'sg':[],'name': 'osd.12','nocheck':True,"take":""},
    #     {'parent_id': [-6], 'type': 0,'type_name':"type0", 'id': 15, 'sg':[],'name': 'osd.15','nocheck':True,"take":""},
    #     {'parent_id': [-6], 'type': 0,'type_name':"type0", 'id': 14, 'sg':[],'name': 'osd.14','nocheck':True,"take":""},
    #     {'parent_id': [-6], 'type': 0,'type_name':"type0", 'id': 17, 'sg':[],'name': 'osd.17','nocheck':True,"take":""},
    #     {'parent_id': [-6], 'type': 0,'type_name':"type0", 'id': 16, 'sg':[],'name': 'osd.16','nocheck':True,"take":""},
    #     {'parent_id': [-6], 'type': 0,'type_name':"type0", 'id': 18, 'sg':[],'name': 'osd.18','nocheck':True,"take":""},
    #     {'parent_id': [-7], 'type': 0,'type_name':"type0", 'id': 32, 'sg':[],'name': 'osd.32','nocheck':True,"take":""},
    #     {'parent_id': [-7], 'type': 0,'type_name':"type0", 'id': 31, 'sg':[],'name': 'osd.31','nocheck':True,"take":""},
    #     {'parent_id': [-7], 'type': 0,'type_name':"type0", 'id': 30, 'sg':[],'name': 'osd.30','nocheck':True,"take":""},
    #     {'parent_id': [-8], 'type': 0,'type_name':"type0", 'id': 22, 'sg':[],'name': 'osd.22','nocheck':True,"take":""},
    #     {'parent_id': [-9], 'type': 0,'type_name':"type0", 'id': 25, 'sg':[],'name': 'osd.25','nocheck':True,"take":""},
    #     {'parent_id': [-9], 'type': 0,'type_name':"type0", 'id': 26, 'sg':[],'name': 'osd.26','nocheck':True,"take":""},
    #     {'parent_id': [-9], 'type': 0,'type_name':"type0", 'id': 27, 'sg':[],'name': 'osd.27','nocheck':True,"take":""},
    #     {'parent_id': [-9], 'type': 0,'type_name':"type0", 'id': 23, 'sg':[],'name': 'osd.23','nocheck':True,"take":""},
    #     {'parent_id': [-9], 'type': 0,'type_name':"type0", 'id': 28, 'sg':[],'name': 'osd.28','nocheck':True,"take":""},
    #     {'parent_id': [-9], 'type': 0,'type_name':"type0", 'id': 29, 'sg':[],'name': 'osd.29','nocheck':True,"take":""},
    #     {'parent_id': [-9,-8], 'type': 0,'type_name':"type0", 'id': 24, 'sg':[],'name': 'osd.24','nocheck':True,"take":""},
    # ]
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
        # _sg1 = {
        #     "id":1,
        #     "name":"sg1",
        #     "storage_class":"class1",
        #     "friendly_name":"name1",
        #     "marker":"#50f50f",
        #     "take_list":[
        #         {
        #             "id":-7,
        #             "name":"ceph03_performance_zone0",
        #             "??":1,
        #             "choose_type":"type1",
        #             "choose_num":12
        #         },
        #         {
        #             "id":-12,
        #             "name":"zone0_capacity",
        #             "type_id":1,
        #             "type_name":"type1",
        #             "choose_num":34
        #         }
        #     ]
        # }
        # _sgs.append(_sg1)
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
