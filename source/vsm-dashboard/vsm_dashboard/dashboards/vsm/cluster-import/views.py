import logging
import os
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy

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

class ImportClusterView(forms.ModalFormView):
    form_class = ImportCluster
    template_name = 'vsm/cluster-import/import_cluster.html'
    success_url = reverse_lazy('horizon:vsm:poolsmanagement:index')


def import_cluster(request):
    status = ""
    msg = ""
    body = json.loads(request.body)
    print "=========import cluster data========"
    print body
    try:
        code,ret = vsmapi.import_cluster(request,body=body)
        print '============='
        print ret
        print '!!!!!!!!!!!'

        if ret.get('error'):
            print 'ecept----1111-----'
            status = "Failed"
            msg = ret.get('error')
            print 'ecept----22222-----'
        else:
            status = "OK"
            msg = "Import Cluster Successfully!"
    except:
        print 'ecept---------'
        raise
        status = "Failed"
        msg = "Import Cluster Failed!"

    resp = dict(message=msg, status=status)
    print resp
    resp = json.dumps(resp)
    return HttpResponse(resp)

def check_cluster_tobe_import(request):
    status = ""
    msg = ""
    body = json.loads(request.body)
    print "=========check cluster data========"
    print body
    try:
        ret = vsmapi.check_pre_existing_cluster(request,body=body)
        print '============='
        print ret
        print '!!!!!!!!!!!'
        if ret.get('error'):
            status = "Failed"
            msg = ret.get('error')
        else:
            status = "OK"
            msg = "Import Cluster Successfully!"
    except:
        status = "Failed"
        msg = "Import Cluster Failed!"

    resp = dict(message=msg, status=status)
    resp = json.dumps(resp)
    return HttpResponse(resp)