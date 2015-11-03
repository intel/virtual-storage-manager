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
import os
import commands

try:
    from novaclient.v1_1 import client as nc
except:
    from novaclient.v2 import client as nc

try:
    from cinderclient.v1 import client as cc
except:
    from cinderclient.v2 import client as cc

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

def _get_token(tenant_name, username, password, auth_url, region_name):
    """Get auth info from keystone."""
    public_url = None
    auth_url = auth_url + "/tokens"
    auth_data = {
        "auth": {
            "tenantName": tenant_name,
            "passwordCredentials": {
                "username": username,
                "password": password
            }
        }
    }

    auth_request = urllib2.Request(auth_url)
    auth_request.add_header("content-type", "application/json")
    auth_request.add_header('Accept', 'application/json')
    auth_request.add_header('User-Agent', 'python-mikeyp')
    auth_request.add_data(json.dumps(auth_data))
    auth_response = urllib2.urlopen(auth_request)
    response_data = json.loads(auth_response.read())

    token = response_data['access']['token']['id']

    service_list = response_data['access']['serviceCatalog']
    for service in service_list:
        if service['type'] == 'volume' and service['name'] == 'cinder':
            for endpoint in service['endpoints']:
                if region_name != None and endpoint['region'] == region_name:
                    public_url = endpoint['publicURL']
                    break
                elif region_name == None or region_name == "" and len(service['endpoints']) == 1:
                    public_url = endpoint['publicURL']
                    break
    if public_url != None:
        url_id = public_url.split('/')[-1]
        return token + "-" + url_id
    else:
        return None

def create(contxt, auth_openstack=None, allow_duplicate=False):
    """create app node from a dict"""
    if contxt is None:
        contxt = context.get_admin_context()

    if not auth_openstack:
        raise exception.AppNodeInvalidInfo()

    os_controller_host = auth_openstack['os_auth_url'].split(":")[1][2:]
    result, err = utils.execute(
            'check_xtrust_crudini',
            auth_openstack['ssh_user'],
            os_controller_host,
            run_as_root = True
    )
    LOG.info("==============result: %s" % result)
    LOG.info("==============err: %s" % err)
    if "command not found" in err:
        raise Exception("Command not found on %s" % os_controller_host)
    if "Permission denied" in err:
        raise Exception("Please check the mutual trust between vsm controller node "
                        "and openstack controller node")
    if "No passwd entry" in err:
        raise Exception("Please check the trust user")

    ref = []

    """validate openstack access info"""
    try:
        token_url_id = _get_token(
            auth_openstack['os_tenant_name'],
            auth_openstack['os_username'],
            auth_openstack['os_password'],
            auth_openstack['os_auth_url'],
            auth_openstack['os_region_name']
        )
        if token_url_id != None:
            auth_openstack['ssh_status'] = "reachable"
        else:
            auth_openstack['ssh_status'] = "no cinder-volume"
    except:
        LOG.exception(_("Error to access to openstack"))
        auth_openstack['ssh_status'] = "unreachable"

    try:
        ref.append(db.appnodes_create(contxt, auth_openstack, allow_duplicate))
    except db_exc.DBError as e:
        LOG.exception(_("DB Error on creating Appnodes %s" % e))
        raise exception.AppNodeFailure()
    return ref

def update(contxt, appnode_id, appnode):
    """update app node ssh status, log info or deleted"""
    if contxt is None:
        contxt = context.get_admin_context()

    id = utils.int_from_str(appnode_id)
    LOG.debug('app node id: %s ' % id)

    os_controller_host = appnode['os_auth_url'].split(":")[1][2:]
    result, err = utils.execute(
            'check_xtrust_crudini',
            appnode['ssh_user'],
            os_controller_host,
            run_as_root = True
    )
    LOG.info("==============result: %s" % result)
    LOG.info("==============err: %s" % err)
    if "command not found" in err:
        raise Exception("Command not found on %s" % os_controller_host)
    if "Permission denied" in err:
        raise Exception("Please check the mutual trust between vsm controller node "
                        "and openstack controller node")
    if "No passwd entry" in err:
        raise Exception("Please check the trust user")

    """validate openstack access info"""
    try:
        token_url_id = _get_token(
            appnode['os_tenant_name'],
            appnode['os_username'],
            appnode['os_password'],
            appnode['os_auth_url'],
            appnode['os_region_name']
        )
        if token_url_id != None:
            appnode['ssh_status'] = "reachable"
        else:
            appnode['ssh_status'] = "no cinder-volume"
    except:
        LOG.exception(_("Error to access to openstack"))
        appnode['ssh_status'] = "unreachable"

    try:
        return db.appnodes_update(contxt, id, appnode)
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
