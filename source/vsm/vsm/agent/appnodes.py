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
App nodes operations.
"""

from vsm import context
from vsm import db
from vsm import utils
from vsm import exception
from vsm.openstack.common.gettextutils import _
from vsm.openstack.common import log as logging
from vsm.openstack.common.db import exception as db_exc

import json
import urllib2

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

def create(contxt, auth_openstack=None, allow_duplicate=False):
    """create app node from a dict"""
    if contxt is None:
        contxt = context.get_admin_context()

    if not auth_openstack:
        raise exception.AppNodeInvalidInfo()

    ref = []

    """validate openstack access info"""

    auth_data = {
        "auth": {
            "tenantName": auth_openstack['os_tenant_name'],
            "passwordCredentials": {
                "username": auth_openstack['os_username'],
                "password": auth_openstack['os_password']
            }
        }
    }
    auth_request = urllib2.Request(auth_openstack['os_auth_url'] + "/tokens")
    auth_request.add_header("content-type", "application/json")
    auth_request.add_header('Accept', 'application/json')
    auth_request.add_header('User-Agent', 'python-mikeyp')
    auth_request.add_data(json.dumps(auth_data))
    try:
        auth_response = urllib2.urlopen(auth_request)
        response_data = json.loads(auth_response.read())
        auth_openstack['ssh_status'] = "reachable"
    except:
        LOG.exception(_("Error to access to openstack"))
        auth_openstack['ssh_status'] = "unreachable"

    try:
        ref.append(db.appnodes_create(contxt, auth_openstack, allow_duplicate))
    except db_exc.DBError as e:
        LOG.exception(_("DB Error on creating Appnodes %s" % e))
        raise exception.AppNodeFailure()
    return ref

def update(contxt, appnode_id, ssh_status=None, log_info=None, os_tenant_name=None,
           os_username=None, os_password=None, os_auth_url=None):
    """update app node ssh status, log info or deleted"""
    if contxt is None:
        contxt = context.get_admin_context()

    id = utils.int_from_str(appnode_id)
    LOG.debug('app node id: %s ' % id)
    kargs = {}

    if os_tenant_name:
        kargs['os_tenant_name'] = os_tenant_name

    if os_username:
        kargs['os_username'] = os_username

    if os_password:
        kargs['os_password'] = os_password

    if os_auth_url:
        kargs['os_auth_url'] = os_auth_url

    # if ssh_status:
    #     utils.check_string_length(ssh_status, 'ssh_status', 1, 50)
    #     kargs['ssh_status'] = ssh_status

    """validate openstack access info"""

    auth_data = {
        "auth": {
            "tenantName": os_tenant_name,
            "passwordCredentials": {
                "username": os_username,
                "password": os_password
            }
        }
    }
    auth_request = urllib2.Request(os_auth_url + "/tokens")
    auth_request.add_header("content-type", "application/json")
    auth_request.add_header('Accept', 'application/json')
    auth_request.add_header('User-Agent', 'python-mikeyp')
    auth_request.add_data(json.dumps(auth_data))
    try:
        auth_response = urllib2.urlopen(auth_request)
        response_data = json.loads(auth_response.read())
        kargs['ssh_status'] = "reachable"
    except:
        LOG.exception(_("Error to access to openstack"))
        kargs['ssh_status'] = "unreachable"

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
