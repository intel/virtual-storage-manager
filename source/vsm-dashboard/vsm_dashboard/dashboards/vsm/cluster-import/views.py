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
from .tables import ListServerTable
from .form import ImportCluster
from django.http import HttpResponse



import json
LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = ListServerTable
    template_name = 'vsm/cluster-import/index.html'

    def get_data(self):
        _servers = []
        try:
            _servers = vsmapi.get_server_list(self.request,)
            _zones = vsmapi.get_zone_list(self.request)
            if _servers:
                logging.debug("resp body in view: %s" % _servers)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve sever list. '))

        zones = {}
        for _zone in _zones:
            zones.setdefault(_zone.id, _zone.name)

        servers = []
        for _server in _servers:
            server = {"id": _server.id,
                        "name": _server.host,
                        "primary_public_ip": _server.primary_public_ip,
                        "secondary_public_ip": _server.secondary_public_ip,
                        "cluster_ip": _server.cluster_ip,
                        "zone_id": _server.zone_id,
                        "zone": "",
                        "osds": _server.osds,
                        "type": _server.type,
                        "status": _server.status}

            if "monitor" in _server.type:
                server['is_monitor'] = "yes"
            else:
                server['is_monitor'] = "no"
            if _server.zone_id in zones:
                server['zone'] = zones[_server.zone_id]
                server['ismonitor'] = ''
                server['isstorage'] = ''
            servers.append(server)
        return servers

class ImportClusterView(views.APIView):
    #form_class = ImportCluster
    template_name = 'vsm/cluster-import/import_cluster.html'

    def get_data(self, request, context, *args, **kwargs):
        context["monitor_host"] = get_monitor_host(request)
        return  context

def get_monitor_host(request):
    monitor_list = []
    try:
        #get the serverlist
        _servers = vsmapi.get_server_list(request,)
        for _server in _servers:
            if "monitor" in _server.type:
                server_item = {
                    "id":_server.id,
                    "host":_server.host
                }
                monitor_list.append(server_item)
    except:
        pass
    return monitor_list


def auto_detect(request):
    status = ""
    msg = ""
    body = json.loads(request.body)
    print body
    try:
        ret = vsmapi.detect_crushmap(request,body=body)
        status = "OK"
        msg = ret[1].get('crushmap')
    except:
        status = "Failed"
        msg = "Auto detect crush map Failed!"

    resp = dict(message=msg, status=status)
    resp = json.dumps(resp)
    return HttpResponse(resp)

def validate_conf(request):
    status = ""
    msg = ""
    body = json.loads(request.body)
    print body
    try:
        ret = vsmapi.check_pre_existing_cluster(request,body=body)
        if ret[1].get('error'):
            status = "Failed"
            msg = ret[1].get('error')
            crushmap_tree_data = ret[1].get('crushmap_tree_data')
        else:
            status = "OK"
            msg = "Validate Cluster Successfully!"
            crushmap_tree_data = ret[1].get('crushmap_tree_data')
    except:
        status = "Failed"
        msg = "Validate Cluster Failed!"

    resp = dict(message=msg, status=status, crushmap_tree_data=crushmap_tree_data )
    resp = json.dumps(resp)
    return HttpResponse(resp)


def import_cluster(request):
    status = ""
    msg = ""
    body = json.loads(request.body)
    try:
        ret = vsmapi.import_cluster(request,body=body)
        if ret[1].get('error'):
            status = "Failed"
            msg = ret[1].get('error')
        else:
            status = "OK"
            msg = "Import Cluster Successfully!"
    except:
        status = "Failed"
        msg = "Import Cluster Failed!"

    resp = dict(message=msg, status=status)
    print resp
    resp = json.dumps(resp)
    return HttpResponse(resp)


def get_crushmap_series():
    node_list = [
        {'type': 4, 'id': -16, 'name': 'vsm'},

        {'parent_id': [-16], 'type': 3, 'id': -13, 'name': 'performance'},
        {'parent_id': [-16], 'type': 3, 'id': -15, 'name': 'capacity'},
        {'parent_id': [-16], 'type': 3, 'id': -14, 'name': 'high_performance_test'},

        {'parent_id': [-14], 'type': 2, 'id': -11, 'name': 'zone0_high_performance_test'},
        {'parent_id': [-13], 'type': 2, 'id': -10, 'name': 'zone0_performance'},
        {'parent_id': [-15], 'type': 2, 'id': -12, 'name': 'zone0_capacity'},

        {'parent_id': [-10], 'type': 1, 'id': -4, 'name': 'ceph02_performance_zone0'},
        {'parent_id': [-10], 'type': 1, 'id': -7, 'name': 'ceph03_performance_zone0'},
        {'parent_id': [-10], 'type': 1, 'id': -1, 'name': 'ceph01_performance_zone0'},
        {'parent_id': [-11], 'type': 1, 'id': -8, 'name': 'ceph03_high_performance_test_zone0'},
        {'parent_id': [-11], 'type': 1, 'id': -5, 'name': 'ceph02_high_performance_test_zone0'},
        {'parent_id': [-11], 'type': 1, 'id': -2, 'name': 'ceph01_high_performance_test_zone0'},
        {'parent_id': [-12], 'type': 1, 'id': -9, 'name': 'ceph03_capacity_zone0'},
        {'parent_id': [-12], 'type': 1, 'id': -3, 'name': 'ceph01_capacity_zone0'},
        {'parent_id': [-12], 'type': 1, 'id': -6, 'name': 'ceph02_capacity_zone0'},

        {'parent_id': [-1], 'type': 0, 'id': 8, 'name': 'osd.8'},
        {'parent_id': [-1], 'type': 0, 'id': 10, 'name': 'osd.10'},
        {'parent_id': [-1], 'type': 0, 'id': 9, 'name': 'osd.9'},
        {'parent_id': [-2], 'type': 0, 'id': 0, 'name': 'osd.0'},
        {'parent_id': [-3], 'type': 0, 'id': 2, 'name': 'osd.2'},
        {'parent_id': [-3], 'type': 0, 'id': 4, 'name': 'osd.4'},
        {'parent_id': [-3], 'type': 0, 'id': 6, 'name': 'osd.6'},
        {'parent_id': [-3], 'type': 0, 'id': 1, 'name': 'osd.1'},
        {'parent_id': [-3], 'type': 0, 'id': 3, 'name': 'osd.3'},
        {'parent_id': [-3], 'type': 0, 'id': 5, 'name': 'osd.5'},
        {'parent_id': [-3], 'type': 0, 'id': 7, 'name': 'osd.7'},
        {'parent_id': [-4], 'type': 0, 'id': 19, 'name': 'osd.19'},
        {'parent_id': [-4], 'type': 0, 'id': 20, 'name': 'osd.20'},
        {'parent_id': [-4], 'type': 0, 'id': 21, 'name': 'osd.21'},
        {'parent_id': [-5], 'type': 0, 'id': 11, 'name': 'osd.11'},
        {'parent_id': [-6], 'type': 0, 'id': 13, 'name': 'osd.13'},
        {'parent_id': [-6], 'type': 0, 'id': 12, 'name': 'osd.12'},
        {'parent_id': [-6], 'type': 0, 'id': 15, 'name': 'osd.15'},
        {'parent_id': [-6], 'type': 0, 'id': 14, 'name': 'osd.14'},
        {'parent_id': [-6], 'type': 0, 'id': 17, 'name': 'osd.17'},
        {'parent_id': [-6], 'type': 0, 'id': 16, 'name': 'osd.16'},
        {'parent_id': [-6], 'type': 0, 'id': 18, 'name': 'osd.18'},
        {'parent_id': [-7], 'type': 0, 'id': 32, 'name': 'osd.32'},
        {'parent_id': [-7], 'type': 0, 'id': 31, 'name': 'osd.31'},
        {'parent_id': [-7], 'type': 0, 'id': 30, 'name': 'osd.30'},
        {'parent_id': [-8], 'type': 0, 'id': 22, 'name': 'osd.22'},
        {'parent_id': [-9], 'type': 0, 'id': 25, 'name': 'osd.25'},
        {'parent_id': [-9], 'type': 0, 'id': 26, 'name': 'osd.26'},
        {'parent_id': [-9], 'type': 0, 'id': 27, 'name': 'osd.27'},
        {'parent_id': [-9], 'type': 0, 'id': 23, 'name': 'osd.23'},
        {'parent_id': [-9], 'type': 0, 'id': 28, 'name': 'osd.28'},
        {'parent_id': [-9], 'type': 0, 'id': 29, 'name': 'osd.29'},
        {'parent_id': [-9,-8], 'type': 0, 'id': 24, 'name': 'osd.24'},
    ]

    #generate the crushmap nodes
    #type: 4-root, 3-storage group, 2-zone, 1-xxx, 0-OSD
    crushmap_nodes = []
    for node in node_list:
        is_parent = False
        is_open = False
        font = ""
        pID_list = node.get("parent_id",["root"])
        for pID in pID_list:
            if pID == "root":
                is_parent = True
                is_open = True
                pID = "root"
            item = {
                "id":node["id"],
                "pId":pID,
                "type":node["type"],
                "name":node["name"],
                "font":"",
                "open":is_open,
                "isParent":is_parent,
            }
            #append the item into crushmap
            crushmap_nodes.append(item)
    return crushmap_nodes