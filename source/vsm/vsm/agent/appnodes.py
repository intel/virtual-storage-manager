# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
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
App nodes operations.
"""

from vsm import context
from vsm import db
from vsm import utils
from vsm import exception
from vsm.openstack.common.gettextutils import _
from vsm.openstack.common import log as logging
from vsm.openstack.common.db import exception as db_exc

LOG = logging.getLogger(__name__)

def get_all_nodes(contxt):
    """get all non-deletd app nodes as a dict"""
    if contxt is None:
        contxt = context.get_admin_context()
    try:
        nodes = db.appnodes_get_all(contxt)
        return nodes
    except db_exc.DBError as e:
        LOG.exception(_("DB Error on getting Appnodes %s" % e))
        raise exception.AppNodeFailure()

def create(contxt, ips=None, allow_duplicate=False):
    """create app node from a dict"""
    if contxt is None:
        contxt = context.get_admin_context()

    if not ips:
        raise exception.AppNodeInvalidInfo()

    """validate Ipv4 address"""
    ref = []
    for ip in ips:
        if not utils.is_valid_ipv4(ip):
            msg = _("Invalid Ipv4 address %s for app node." % ip)
            raise exception.InvalidInput(reason=msg)
        else:
            attr = {
                'ip': ip
            }
            try:
                ref.append(db.appnodes_create(contxt, attr, allow_duplicate))
            except db_exc.DBError as e:
                LOG.exception(_("DB Error on creating Appnodes %s" % e))
                raise exception.AppNodeFailure()
    return ref

def update(contxt, appnode_id, ssh_status=None, log_info=None, ip=None):
    """update app node ssh status, log info or deleted"""
    if contxt is None:
        contxt = context.get_admin_context()

    id = utils.int_from_str(appnode_id)
    LOG.debug('app node id: %s ' % id)
    kargs = {}

    if ip:
        kargs['ip'] = ip

    if ssh_status:
        utils.check_string_length(ssh_status, 'ssh_status', 1, 50)
        kargs['ssh_status'] = ssh_status

    if log_info:
        utils.check_string_length(log_info, 'log_info', 1, 65535)
        kargs['log_info'] = log_info

    if kargs:
        try:
            return db.appnodes_update(contxt, id, kargs)
        except db_exc.DBError as e:
            LOG.exception(_("DB Error on updating Appnodes %s" % e))
            raise exception.AppNodeFailure()

def destroy(contxt, appnode_id):
    if contxt is None:
        contxt = context.get_admin_context()

    appnode_id = utils.int_from_str(appnode_id)
    try:
        db.appnodes_destroy(contxt, appnode_id)
    except db_exc.DBError as e:
        LOG.exception(_("DB Error on deleting Appnodes %s" % e))
        raise exception.AppNodeFailure()
