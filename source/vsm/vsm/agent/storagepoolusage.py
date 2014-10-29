# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel
# All Rights Reserved.
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
"""
Storage pool usage operations.
"""

from vsm import context
from vsm import db
from vsm import utils
from vsm import exception
from vsm.openstack.common import timeutils
from vsm.openstack.common.gettextutils import _
from vsm.openstack.common import log as logging
from vsm.openstack.common.db import exception as db_exc

LOG = logging.getLogger(__name__)

def get_all(contxt):
    """get all non-deleted storage pool usage as a dict"""
    if contxt is None:
        contxt = context.get_admin_context()
    try:
        uses = db.get_storage_pool_usage(contxt)
        return uses
    except db_exc.DBError as e:
        LOG.exception(_("DB Error on getting Storage Pool Usage %s" % e))
        raise exception.StoragePoolUsageFailure()

def create(contxt, pool_list):
    """create storage pool usages"""
    return db.storage_pool_usage_create(contxt, pool_list)

def update(contxt, vsmapp_id, attach_status=None, is_terminate=False):
    """update storage pool usage"""
    if contxt is None:
        contxt = context.get_admin_context()

    if not vsmapp_id:
        raise exception.StoragePoolUsageInvalid()

    is_terminate = utils.bool_from_str(is_terminate)

    kargs = {
        'attach_status': attach_status,
        'terminate_at': timeutils.utcnow() if is_terminate else None
    }

    try:
        return db.storage_pool_usage_update(contxt, vsmapp_id, kargs)
    except db_exc.DBError as e:
        LOG.exception(_("DB Error on updating new storage pool usage %s" % e))
        raise exception.StoragePoolUsageFailure()

def destroy(contxt, id):
    if contxt is None:
        contxt = context.get_admin_context()

    id = utils.int_from_str(id)
    try:
        db.destroy_storage_pool_usage(contxt, id)
    except db_exc.DBError as e:
        LOG.exception(_("DB Error on deleting Pool Usages %s" % e))
        raise exception.StoragePoolUsageFailure()

