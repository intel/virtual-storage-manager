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
from .tables import ListMDSStatusTable
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)

from django.utils.datastructures import SortedDict

from vsm_dashboard.utils import get_time_delta

class ModalSummaryMixin(object):

   def get_context_data(self, **kwargs):
        context = super(ModalSummaryMixin, self).get_context_data(**kwargs)
        return context

class IndexView(ModalSummaryMixin, tables.DataTableView):
    table_class = ListMDSStatusTable
    template_name = 'vsm/mds-status/index.html'

    def get_data(self):
        _servers = []
        #_servers= vsmapi.get_server_list(self.request,)
        _mds_status = []
        try:
            _mds_status = vsmapi.mds_status(self.request)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve sever list. '))

        mds_status = []
        for _mds in _mds_status:
            mds = {"gid": _mds.gid,
                   "id": _mds.id,
                        "name": _mds.name,
                        "state": _mds.state,
                        "address": _mds.address,
                        "updated_at": get_time_delta(_mds.updated_at),
                        }
            mds_status.append(mds)
        return mds_status

