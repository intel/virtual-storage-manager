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

def _check_v3(tenant_name, username, password, auth_url, region_name):
    result = False
    auth_url = auth_url + "/auth/tokens"
    user_id = username
    user_password = password
    project_id = tenant_name
    auth_data = {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "id": user_id,
                        "password": user_password
                    }
                }
            },
            "scope": {
                "project": {
                    "id": project_id
                }
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
    services_list = response_data['token']['catalog']
    for service in services_list:
        service_type = service['type']
        service_name = service['name']
        endpoints_list = service['endpoints']
        if service_type == "volume" and service_name == "cinder":
            region_list = []
            for endpoint in endpoints_list:
                region = endpoint['region']
                if region not in region_list:
                    region_list.append(region)
                if region_name != None and region == region_name:
                    result = True
                    break
            if len(region_list) == 1:
                result = True
                break
    return result

def _check_v2(tenant_name, username, password, auth_url, region_name):
    result = False
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
    service_list = response_data['access']['serviceCatalog']
    for service in service_list:
        if service['type'] == 'volume' and service['name'] == 'cinder':
            for endpoint in service['endpoints']:
                if region_name != None and endpoint['region'] == region_name:
                    result = True
                    break
                elif region_name == None or region_name == "" and len(service['endpoints']) == 1:
                    result = True
                    break
    return result

def create(contxt, auth_openstack=None, allow_duplicate=False):
    """create app node from a dict"""
    if contxt is None:
        contxt = context.get_admin_context()

    appnode = auth_openstack
    if not appnode:
        raise exception.AppNodeInvalidInfo()

    auth_url = appnode['os_auth_url'].strip("/")
    ssh_user = appnode['ssh_user']
    tenant_name = appnode['os_tenant_name']
    username = appnode['os_username']
    password = appnode['os_password']
    region_name = appnode['os_region_name']

    os_controller_host = auth_url.split(":")[1][2:]
    result, err = utils.execute(
        'check_xtrust_crudini',
        ssh_user,
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

    # support keystone v3 ad v2.0
    keystone_version = auth_url.split("/")[-1]
    try:
        if keystone_version == "v3":
            result = _check_v3(tenant_name,
                               username,
                               password,
                               auth_url,
                               region_name)
        elif keystone_version == "v2.0":
            result = _check_v2(tenant_name,
                               username,
                               password,
                               auth_url,
                               region_name)
        else:
            raise Exception("Only support keystone v3 and v2.0 now.")
        if result:
            appnode['ssh_status'] = "reachable"
        else:
            appnode['ssh_status'] = "no cinder-volume"
    except:
        LOG.exception(_("Error to access to openstack"))
        appnode['ssh_status'] = "unreachable"

    ref = []
    try:
        ref.append(db.appnodes_create(contxt, appnode, allow_duplicate))
    except db_exc.DBError as e:
        LOG.exception(_("DB Error on creating Appnodes %s" % e))
        raise exception.AppNodeFailure()
    return ref

def update(contxt, appnode_id, appnode):
    """update app node ssh status, log info or deleted"""
    if contxt is None:
        contxt = context.get_admin_context()

    auth_url = appnode['os_auth_url'].strip("/")
    ssh_user = appnode['ssh_user']
    tenant_name = appnode['os_tenant_name']
    username = appnode['os_username']
    password = appnode['os_password']
    region_name = appnode['os_region_name']

    id = utils.int_from_str(appnode_id)
    LOG.debug('app node id: %s ' % id)

    os_controller_host = auth_url.split(":")[1][2:]
    result, err = utils.execute(
            'check_xtrust_crudini',
            ssh_user,
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

    # support keystone v3 ad v2.0
    keystone_version = auth_url.split("/")[-1]
    try:
        if keystone_version == "v3":
            result = _check_v3(tenant_name,
                               username,
                               password,
                               auth_url,
                               region_name)
        elif keystone_version == "v2.0":
            result = _check_v2(tenant_name,
                               username,
                               password,
                               auth_url,
                               region_name)
        else:
            raise Exception("Only support keystone v3 and v2.0 now.")
        if result:
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
