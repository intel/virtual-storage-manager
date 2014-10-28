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
import sys
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy
from django.utils.datastructures import SortedDict
from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import views

from vsm_dashboard.api import vsm as vsmapi
from .tables import OsdsTable
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = OsdsTable
    template_name = 'vsm/devices-management/index.html'

    def get_data(self):
        default_limit = 10000;
        default_sort_dir = "asc";
        default_sort_keys = ['osd_name']
        marker = self.request.GET.get('marker', "")
        try:
            _osds = vsmapi.osd_status(self.request, paginate_opts={
                "limit": default_limit,
                "sort_dir": default_sort_dir,
                "marker":   marker,
            })
        except:
            _osds = []
            exceptions.handle(self.request,
                              _('Unable to retrieve osds. '))
        if _osds:
            logging.error("resp osds in view: %s" % _osds)
        osds = []
        for _osd in _osds:
            osd = {
                    'id': _osd.id,
                    'osd': _osd.osd_name,
                    'vsm_status': _osd.operation_status,
                    'osd_state': _osd.state,
                    'osd_weight': _osd.weight,
                    'storage_group': _osd.device['device_type'],
                    'data_dev_path': _osd.device['path'],
                    'data_dev_status': _osd.device['state'],
                    'data_dev_capacity': 0 if not _osd.device['total_capacity_kb']\
            else int(_osd.device['total_capacity_kb']/1024),
                    'data_dev_used': 0 if not _osd.device['used_capacity_kb']\
            else int(_osd.device['used_capacity_kb']/1024),
                    'data_dev_available': 0 if not _osd.device['avail_capacity_kb']\
            else int(_osd.device['avail_capacity_kb']/1024),
                    'journal_device_path': _osd.device['journal'],
                    'journal_device_status': _osd.device['journal_state'], 
                    'server': _osd.service['host'],
                    'zone': _osd.zone,
                  }
            osds.append(osd)
        return osds

