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
from .tables import ListPoolStatusTable
from django.http import HttpResponse

import json
LOG = logging.getLogger(__name__)
from vsm_dashboard.utils import get_time_delta

class IndexView(tables.DataTableView):
    table_class = ListPoolStatusTable
    template_name = 'vsm/pool-status/index.html'

    def get_data(self):
        #_pool.= vsmapi.get_pool.list(self.request,)
        _pool_status = []
        try:
            _pool_status = vsmapi.pool_status(self.request)
            if _pool_status:
                logging.debug("resp body in view: %s" % _pool_status)
        except:
            exceptions.handle(self.request,
                              _('Unable to retrieve sever list. '))

        pool_status = []
        for _pool in _pool_status:
            pool = {"id": _pool.poolId,
                        "name": _pool.name,
                        "tag": _pool.tag,
                        "storage_group": _pool.storageGroup,
                        "size": _pool.size,
                        "pg_count": _pool.pgNum,
                        "pgp_count": _pool.pgpNum,
                        "create_by": _pool.createdBy,
                        "kb_used": (_pool.num_bytes / 1024 + 1) if _pool.num_bytes else 0,
                        "objects": _pool.num_objects,
                        "clones": _pool.num_object_clones,
                        "degraded": _pool.num_objects_degraded,
                        "unfound": _pool.num_objects_unfound,
                        "read_ops": _pool.num_read,
                        "read_kb": _pool.num_read_kb,
                        "write_ops": _pool.num_write,
                        "write_kb": _pool.num_write_kb,
                        "client_read_b": _pool.read_bytes_sec,
                        "client_write_b": _pool.write_bytes_sec,
                        "client_ops": _pool.op_per_sec,
                        "status": _pool.status,
                        "updated_at": get_time_delta(_pool.updated_at),
                        }

            pool_status.append(pool)
        pool_status = sorted(pool_status, lambda x,y: cmp(x['id'], y['id']))
        return pool_status

