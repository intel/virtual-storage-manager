
# Copyright 2014 Intel Corporation, All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the"License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

import json

from django import http
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from vsm_dashboard.dashboards.vsm.flocking import utils
from .tables import FlockingInstancesTable
from .tables import ListRecipeTable
from .tabs import FlockingTabs

class IndexView(tabs.TabbedTableView):
    tab_group_class = FlockingTabs
    table_class = ListRecipeTable
    template_name = 'vsm/flocking/index.html'

    def get(self, request, *args, **kwargs):
        if self.request.is_ajax() and self.request.GET.get("json", False):
            try:
                #instances = ['kidding', 'you',]
                instances = utils.get_instances_data(self.request)
                # Uncomment the following line to use fake test data.
                #instances = utils.get_fake_instances_data(self.request)
            except:
                instances = []
                exceptions.handle(request,
                                  _('Unable to retrieve instance list.'))
            data = json.dumps([i._apiresource._info for i in instances])
            return http.HttpResponse(data)
        else:
            return super(IndexView, self).get(request, *args, **kwargs)
