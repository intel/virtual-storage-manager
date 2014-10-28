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

from horizon import exceptions
from horizon import tables
from horizon import forms
from horizon import views

from vsm_dashboard.api import vsm as vsmapi
from .tables import ListZoneTable
from .forms import CreateZoneForm
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)

class IndexView(tables.DataTableView):
    table_class = ListZoneTable
    template_name = 'vsm/zonemgmt/index.html'

    def get_data(self):
        try:
            _zones = vsmapi.get_zone_list(self.request)
        except:
            exceptions.handle(self.request,
                   _('Unable to retrieve zone list. '))

        zone_list = []
        for _zone in _zones:
            zone = {"id": _zone.id,
                    "name": _zone.name,}
            zone_list.append(zone)

        return zone_list

class CreateView(forms.ModalFormView):
    LOG.error("DEBUG in CreateView")
    form_class = CreateZoneForm
    template_name = 'vsm/flocking/createzone.html'
    success_url = reverse_lazy('horizon:vsm:zonemgmt:index')

