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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon.utils import functions as utils

from vsm_dashboard.api import vsm as vsmapi
from vsm_dashboard.utils import get_time_delta
from .tables import ListRBDStatusTable

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = ListRBDStatusTable
    template_name = 'vsm/rbd-status/index.html'

    def get_data(self):
        default_limit = utils.get_page_size(self.request)
        default_sort_dir = "asc"
        marker = self.request.GET.get('marker', "")

        _rbd_status = []
        try:
            _rbd_status = vsmapi.rbd_pool_status(self.request, paginate_opts={
                "limit": default_limit,
                "sort_dir": default_sort_dir,
                "marker":   marker,
            })

            if _rbd_status:
                logging.debug("resp body in view: %s" % _rbd_status)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve sever list. '))

        rbd_status = []
        for _rbd in _rbd_status:
            rbd = {
                      "id": _rbd.id,
                      "pool": _rbd.pool,
                      "image_name": _rbd.image_name,
                      "size": _rbd.size/(1024*1024),
                      "objects": _rbd.objects,
                      "order": _rbd.order,
                      "format": _rbd.format,
                      "updated_at": get_time_delta(_rbd.updated_at),
                      }

            rbd_status.append(rbd)
        return rbd_status

