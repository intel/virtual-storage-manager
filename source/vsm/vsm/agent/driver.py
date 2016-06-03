# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at:
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# pylint: disable=R0914
# pylint: disable=R0913

"""
Drivers for testdbs.

"""

import json
import operator
import os
import platform
import time
import urllib2

from vsm.agent import cephconfigparser
from vsm.agent.crushmap_parser import CrushMap
from vsm.agent import rpcapi as agent_rpc
from vsm.common import ceph_version_utils
from vsm.common import constant
from vsm import conductor
from vsm.conductor import rpcapi as conductor_rpcapi
from vsm import db
from vsm import exception
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.openstack.common.rpc import common as rpc_exc
from vsm import utils

try:
    from novaclient.v1_1 import client as nc
except:
    from novaclient.v2 import client as nc

try:
    from cinderclient.v1 import client as cc
except:
    from cinderclient.v2 import client as cc

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS


class CephDriver(object):
    """Excute commands relating to Ceph."""
    def __init__(self):
        self._crushmap_mgmt = CreateCrushMapDriver()
        self._conductor_api = conductor.API()
        self._conductor_rpcapi = conductor_rpcapi.ConductorAPI()
        self._agent_rpcapi = agent_rpc.AgentAPI()
        try:
            cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        except:
            pass

    def _is_systemctl(self):
        """

        if the ceph version is greater than or equals infernalis and the operating
        system is not ubuntu, use command "systemctl" to operate ceph daemons.
        """

        ceph_version = self.get_ceph_version()
        if int(ceph_version.split(".")[0]) > 0:
            utils.execute('chown', '-R', 'ceph:ceph',
                          '/var/lib/ceph', run_as_root=True)
            utils.execute('chown', '-R', 'ceph:ceph',
                          '/etc/ceph', run_as_root=True)
            (distro, release, codename) = platform.dist()
            if distro != "Ubuntu":
                return True
        return False

    def _operate_ceph_daemon(self, operate, type, id=None, ssh=False, host=None):
        """
        start/stop ceph-$type id=$id.
        service ceph start/stop $type.$id
        systemctl start/stop ceph-$type@$id
        ceph script has -a parameter. It can operate remote node. But ceph-$type
        only can operate local node. So using ssh to operate remote node.

        :param operate: start or stop
        :param type: osd, mon or mds or None
        :param id:
        :param ssh: if ssh, then remote operate
        :param host: ssh host
        :return:
        """

        # the cluster should be passed in, but most of the code in this module
        # assumes the cluster is named 'ceph' - just creating a variable here
        # makes it simpler to fix this issue later - at least in this function
        DEFAULT_CLUSTER_NAME = "ceph"
        DEFAULT_OSD_DATA_DIR = "/var/lib/ceph/osd/$cluster-$id"
        DEFAULT_MON_DATA_DIR = "/var/lib/ceph/mon/$cluster-$host"

        # type and id is required here.
        # not support operate all ceph daemons
        if not type or not id:
            LOG.error("Required parameter type or id is blank")
            return False

        # host is local host if not specified
        if not host:
            host = platform.node()

        # get cluster from config - use default if not found
        cluster = DEFAULT_CLUSTER_NAME

        LOG.info("Operate %s type %s, id %s" % (operate, type, id))
        is_systemctl = self._is_systemctl()

        ceph_config_parser = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        data_dir = ceph_config_parser._parser.get(type, type + " data")
        if not data_dir:
            data_dir = DEFAULT_OSD_DATA_DIR if type == "osd" else DEFAULT_MON_DATA_DIR
        # path = os.path.dirname(data_dir)

        file = data_dir.replace("$cluster", cluster).\
                    replace("$id", str(id)).replace("$host", host) + "/upstart"
        # no using os.path.exists(), because if the file is owned by ceph
        # user, the result will return false
        if ssh:
            try:
                out, err = utils.execute('ssh', '-t', 'root@'+host,
                                         'ls', file, run_as_root=True)
            except:
                out = ""
        else:
            try:
                out, err = utils.execute('ls', file, run_as_root=True)
            except:
                out = ""

        # is_file_exist = os.path.exists(file)
        if out:
            id_assignment = "id=%s" % (host if "-$host" in data_dir else id)
            cluster_assignment = "cluster=%s" % cluster
            service = "ceph-%s" % type
            if ssh:
                utils.execute('ssh', '-t', 'root@'+host,
                                  operate, service, cluster_assignment,
                                  id_assignment, run_as_root=True)
            else:
                utils.execute(operate, service, cluster_assignment,
                                  id_assignment, run_as_root=True)
        else:
            if is_systemctl:
                if ssh:
                    utils.execute('ssh', '-t', 'root@'+host,
                                  'systemctl', operate,
                                  'ceph-'+type+'@'+id,
                                  run_as_root=True)
                else:
                    utils.execute('systemctl', operate,
                                  'ceph-'+type+'@'+id,
                                  run_as_root=True)
            else:
                type_id = type + "." + id
                if ssh:
                    utils.execute('ssh', '-t', 'root@'+host,
                                  'service', 'ceph', operate,
                                  type_id, run_as_root=True)
                else:
                    utils.execute('service', 'ceph', operate, type_id,
                                  run_as_root=True)

    def _get_new_ruleset(self):
        args = ['ceph', 'osd', 'crush', 'rule', 'dump']
        ruleset_list = self._run_cmd_to_json(args)
        return len(ruleset_list)
    def _get_cluster_name(self,secondary_public_ip,keyring):
        cluster_name = ''
        args = ['ceph', 'mon', 'dump','--keyring',keyring]
        mon_name = None
        mon_dump = self._run_cmd_to_json(args)
        for mon in mon_dump['mons']:
            if mon['addr'].split(':')[0] == secondary_public_ip.split(',')[0]:
                mon_name = mon['name']
                break
        if mon_name:
            mon_configs = self._get_mon_config_dict(mon_name)
            cluster_name = mon_configs['cluster']
        return cluster_name

    # def _get_ceph_admin_keyring_from_file(self,secondary_public_ip):
    #     keyring = ''
    #     args = ['ceph', 'mon', 'dump']
    #     mon_name = None
    #     mon_dump = self._run_cmd_to_json(args)
    #     for mon in mon_dump['mons']:
    #         if mon['addr'].split(':')[0] == secondary_public_ip.split(',')[0]:
    #             mon_name = mon['name']
    #             break
    #     if mon_name:
    #         mon_configs = self._get_mon_config_dict(mon_name)
    #         keyring_file = mon_configs['keyring']
    #         keyring,err = utils.execute('cat',keyring_file,run_as_root=True)
    #     return keyring

    def _get_mon_config_dict(self,mon_id):
        args = ['ceph', 'daemon','mon.%s'%mon_id ,'config','show']
        return self._run_cmd_to_json(args)





    def create_storage_pool(self, context, body):
        pool_name = body["name"]
        primary_storage_group = ''
        if body.get("ec_profile_id"):
            profile_ref = db.ec_profile_get(context, body['ec_profile_id'])
            pgp_num = pg_num = profile_ref['pg_num'] 
            plugin = "plugin=" + profile_ref['plugin']

            crushmap = self.get_crushmap_json_format()
            ruleset_root = "ruleset-root=" +  crushmap.get_bucket_root_by_rule_name(body['ec_ruleset_root'])
            failure_domain = "ruleset-failure-domain=" + body['ec_failure_domain']
            rule_name = pool_name

            kv = eval(profile_ref['plugin_kv_pair'])
            pair_str = ""
            for k, v in kv.items():
               pair_str += str(k) + "=" + str(v) + " " 
    
            utils.execute('ceph', 'osd', 'erasure-code-profile','set', profile_ref['name'], \
                            plugin, ruleset_root, failure_domain, pair_str, '--force', \
                            run_as_root=True)

            utils.execute('ceph', 'osd', 'crush', 'rule', 'create-erasure', \
                            rule_name, profile_ref['name'], run_as_root=True)

            res = utils.execute('ceph', 'osd', 'pool', 'create', pool_name, pg_num, \
                            pgp_num, 'erasure', profile_ref['name'], rule_name, \
                            run_as_root=True)
            new_crushmap = self.get_crushmap_json_format()
            storage_group_values = new_crushmap.get_storage_group_value_by_rule_name(rule_name)
            if len(storage_group_values) == 1:
                storage_group_values = storage_group_values[0]
                storage_group_values['status'] = 'IN'
                ref_storge_group = db.storage_group_update_or_create(context,storage_group_values)
                body['storage_group_id'] = ref_storge_group.id
        elif body.get('pool_type') == 'replicated':
            try:
                utils.execute('ceph', 'osd', 'getcrushmap', '-o', FLAGS.crushmap_bin,
                                run_as_root=True)
                utils.execute('crushtool', '-d', FLAGS.crushmap_bin, '-o', FLAGS.crushmap_src, 
                                run_as_root=True)
                #ruleset = self._get_new_ruleset()
                pg_num = str(body['pg_num'])
                primary_storage_group = body['storage_group_name']
                storage_group = db.storage_group_get_by_name(context,primary_storage_group)
                ruleset = storage_group['rule_id']
                utils.execute('chown', '-R', 'vsm:vsm', '/etc/vsm/',
                        run_as_root=True) 

                utils.execute('ceph', 'osd', 'pool', 'create', pool_name, \
                            pg_num, pg_num, 'replicated', run_as_root=True)
                utils.execute('ceph', 'osd', 'pool', 'set', pool_name,
                            'crush_ruleset', ruleset, run_as_root=True)
                utils.execute('ceph', 'osd', 'pool', 'set', pool_name,
                            'size', str(body['size']), run_as_root=True)
                res = True
            except:
                LOG.error("create replica storage pool error!")
                raise
                return False  
        else:
            rule = str(body['crush_ruleset'])
            size = str(body['size'])
            pg_num = str(body['pg_num'])
            res = utils.execute('ceph', 'osd', 'pool', 'create', pool_name, \
                                pg_num, run_as_root=True)
            utils.execute('ceph', 'osd', 'pool', 'set', pool_name,
                            'size', size, run_as_root=True)
            utils.execute('ceph', 'osd', 'pool', 'set', pool_name,
                            'crush_ruleset', rule, run_as_root=True)
        #set quota
        if body.get('enable_quota', False):
            max_bytes = 1024 * 1024 * 1024 * int(body.get('quota', 0))
            utils.execute('ceph', 'osd', 'pool', 'set-quota', pool_name, 'max_bytes', max_bytes,\
                            run_as_root=True)  
        #update db
        pool_list = self.get_pool_status()
        for pool in pool_list:
            if pool_name == pool['pool_name']:
                values = {
                        'pool_id': pool.get('pool'),
                        'name': pool.get('pool_name'),
                        'pg_num': pool.get('pg_num'),
                        'pgp_num': pool.get('pg_placement_num'),
                        'size': pool.get('size'),
                        'min_size': pool.get('min_size'),
                        'crush_ruleset': pool.get('crush_ruleset'),
                        'crash_replay_interval': pool.get('crash_replay_interval'),
                        'ec_status': pool.get('erasure_code_profile'),
                        'replica_storage_group': body.get('pool_type'),
                        'quota': body.get('quota'),
                        'max_pg_num_per_osd':body.get('max_pg_num_per_osd'),
                        'auto_growth_pg':body.get('auto_growth_pg',0),
                }
                values['created_by'] = body.get('created_by')
                values['cluster_id'] = body.get('cluster_id')
                values['tag'] = body.get('tag')
                values['status'] = 'running'
                values['primary_storage_group_id'] = body.get('storage_group_id')
                db.pool_create(context, values)

        return res

    def _keystone_v3(self, tenant_name, username, password,
                     auth_url, region_name):
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
        return auth_response

    def _keystone_v2(self, tenant_name, username, password,
                     auth_url, region_name):
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
        return auth_response

    def _config_cinder_conf(self, **kwargs):
        LOG.info("_config_cinder_conf")
        uuid = kwargs.pop('uuid', None)
        volume_host = kwargs.pop('volume_host', None)
        pool_type = kwargs.pop('pool_type', None)
        pool_name = kwargs.pop('pool_name', None)
        ssh_user = kwargs.pop('ssh_user', None)
        os_controller_host = kwargs.pop('os_controller_host', None)

        pool_str = pool_name + "," + pool_type + "-" + pool_name
        LOG.info("volume host = %s, uuid = %s, pool type = %s, pool name = %s, "
                 "ssh_user = %s, os_controller_host = %s" %
                 (volume_host, uuid, pool_type, pool_name, ssh_user,
                  os_controller_host))
        LOG.info("present pool info = %s" % pool_str)

        try:
            out, err = utils.execute(
                'presentpool',
                'cinder',
                ssh_user,
                uuid,
                volume_host,
                os_controller_host,
                pool_str,
                run_as_root = True
            )
            LOG.info("present pool on cinder-volume host logs = %s" % out)
        except:
            LOG.error("Failed to present pool on cinder-volume host")
            pass


    def _config_nova_conf(self, **kwargs):
        LOG.info("_config_nova_conf")
        uuid = kwargs.pop('uuid', "")
        username = kwargs.pop('username', "")
        password = kwargs.pop('password', "")
        tenant_name = kwargs.pop('tenant_name', "")
        auth_url = kwargs.pop('auth_url', "")
        region_name = kwargs.pop('region_name', "")
        ssh_user = kwargs.pop('ssh_user', None)
        os_controller_host = kwargs.pop('os_controller_host', None)
        nova_compute_hosts = []

        LOG.info("uuid = %s, username = %s, password = %s, tenant name = %s, "
        "auth url = %s, region name = %s, ssh_user = %s, os_controller_host = %s" %
                 (uuid, username, password, tenant_name, auth_url, region_name,
                  ssh_user, os_controller_host))
        if "v3" in auth_url:
            connection = self._keystone_v3(tenant_name, username, password, auth_url, region_name)
            response_data = json.loads(connection.read())
            services_list = response_data['token']['catalog']
            endpoints_list = []
            _url = None
            for service in services_list:
                service_type = service['type']
                service_name = service['name']
                if service_type == "compute" and service_name == "nova":
                    endpoints_list = service['endpoints']
                    break
            for endpoint in endpoints_list:
                interface = endpoint['interface']
                region_id = endpoint['region_id']
                if region_name:
                    if interface == "public" and region_id == region_name:
                        _url = endpoint['url']
                        break
                else:
                    if len(endpoints_list) == 3:
                        _url = endpoint['url']
                        break
            token = connection.info().getheader('X-Subject-Token')
            url_list = _url.split(":")
            auth_url_list = auth_url.split(":")
            url_list[1] = auth_url_list[1]
            url = ":".join(url_list) + "/os-services"
            req = urllib2.Request(url)
            req.get_method = lambda: 'GET'
            req.add_header("content-type", "application/json")
            req.add_header("X-Auth-Token", token)
            resp = urllib2.urlopen(req)
            nova_services = json.loads(resp.read())
            nova_services = nova_services['services']
            LOG.info("nova services = %s " % str(nova_services))
            for nova_service in nova_services:
                if nova_service['binary'] == "nova-compute":
                    nova_compute_hosts.append(nova_service['host'])
            LOG.info("nova-compute hosts = %s" % str(nova_compute_hosts))
        else:
            novaclient = nc.Client(
                username, password, tenant_name, auth_url, region_name=region_name
            )
            nova_services = novaclient.services.list()
            LOG.info("nova services = %s " % str(nova_services))
            for nova_service in nova_services:
                if nova_service.binary == "nova-compute":
                    nova_compute_hosts.append(nova_service.host)
            LOG.info("nova-compute hosts = %s" % str(nova_compute_hosts))

        for nova_compute_host in nova_compute_hosts:
            try:
                LOG.info("nova-compute host = %s" % nova_compute_host)
                out, err = utils.execute(
                    'presentpool',
                    'nova',
                    ssh_user,
                    uuid,
                    nova_compute_host,
                    os_controller_host,
                    run_as_root = True
                )
                LOG.info("present pool on nova-compute host logs = %s" % out)
            except:
                LOG.info("Failed to present pool on nova-compute host")
                pass

    def _config_glance_conf(self, **kwargs):
        LOG.info("_config_glance_conf")
        uuid = kwargs.pop('uuid', "")
        pool_name = kwargs.pop('pool_name', "")
        os_controller_host = kwargs.pop('os_controller_host', "")
        tenant_name = kwargs.pop('tenant_name', "")
        username = kwargs.pop('username', "")
        password = kwargs.pop('password', "")
        auth_url = kwargs.pop('auth_url', "")
        region_name = kwargs.pop('region_name', "")
        ssh_user = kwargs.pop('ssh_user', "")

        _url = None
        if "v3" in auth_url:
            connection = self._keystone_v3(tenant_name, username, password, auth_url, region_name)
            response_data = json.loads(connection.read())
            services_list = response_data['token']['catalog']
            endpoints_list = []
            for service in services_list:
                service_type = service['type']
                service_name = service['name']
                if service_type == "image" and service_name == "glance":
                    endpoints_list = service['endpoints']
                    break
            for endpoint in endpoints_list:
                interface = endpoint['interface']
                region_id = endpoint['region_id']
                if region_name:
                    if interface == "public" and region_id == region_name:
                        _url = endpoint['url']
                        break
                else:
                    if len(endpoints_list) == 3:
                        _url = endpoint['url']
                        break
            pass
        elif "v2.0" in auth_url:
            connection = self._keystone_v2(tenant_name, username, password, auth_url, region_name)
            response_data = json.loads(connection.read())
            services_list = response_data['access']['serviceCatalog']
            endpoints_list = []
            for service in services_list:
                service_type = service['type']
                service_name = service['name']
                if service_type == "image" and service_name == "glance":
                    endpoints_list = service['endpoints']
                    break
            for endpoint in endpoints_list:
                region = endpoint['region']
                if region == region_name:
                    _url = endpoint['publicURL']
                    break
        glance_host = _url.split("/")[2].split(":")[0]
        LOG.info("uuid = %s, glance_host = %s, pool_name = %s, os_controller_host = %s, "
                 "ssh_user = %s" % (uuid, glance_host, pool_name, os_controller_host, ssh_user))
        try:
            out, err = utils.execute(
                'presentpool',
                'glance',
                ssh_user,
                uuid,
                glance_host,
                os_controller_host,
                pool_name,
                run_as_root=True
            )
            LOG.info("present pool on glance-api host logs = %s" % out)
        except:
            LOG.info("Failed to present pool on glance-api host")
            pass

    def present_storage_pools(self, context, info):
        LOG.info('agent present_storage_pools()')
        LOG.info('body = %s' % info)

        regions = {}
        for pool in info:
            as_glance_store_pool = pool['as_glance_store_pool']
            appnode_id = pool['appnode_id']
            appnode = db.appnodes_get_by_id(context, appnode_id)
            volume_host = pool['cinder_volume_host']
            tenant_name = appnode['os_tenant_name']
            username = appnode['os_username']
            password = appnode['os_password']
            auth_url = appnode['os_auth_url']
            region_name = appnode['os_region_name']
            os_controller_host = auth_url.split(":")[1][2:]
            pool_type = pool['pool_type']
            pool_name = pool['pool_name']
            uuid = appnode['uuid']
            ssh_user = appnode['ssh_user']

            # if is_glance_store_pool, present pool for openstack glance
            if as_glance_store_pool:
                self._config_glance_conf(uuid=uuid,
                                         pool_name=pool_name,
                                         os_controller_host=os_controller_host,
                                         username=username,
                                         password=password,
                                         tenant_name=tenant_name,
                                         auth_url=auth_url,
                                         region_name=region_name,
                                         ssh_user=ssh_user)

            if not volume_host:
                return

            # present pool for openstack cinder
            self._config_cinder_conf(uuid=uuid,
                                     volume_host=volume_host,
                                     pool_type=pool_type,
                                     pool_name=pool_name,
                                     ssh_user=ssh_user,
                                     os_controller_host=os_controller_host
                                     )

            # only config nova.conf at the first time
            if region_name not in regions.keys() or (
                region_name in regions.keys() and
                            os_controller_host != regions.get(region_name)):
                regions.update({region_name: os_controller_host})
                self._config_nova_conf(uuid=uuid,
                                       username=username,
                                       password=password,
                                       tenant_name=tenant_name,
                                       auth_url=auth_url,
                                       region_name=region_name,
                                       ssh_user=ssh_user,
                                       os_controller_host=os_controller_host
                                       )

            volume_type = pool_type + "-" + pool_name
            if "v3" in auth_url:
                def _get_volume_type_list():
                    volume_type_list = []
                    i = 0
                    while i < 60:
                        try:
                            connection = self._keystone_v3(tenant_name, username, password,
                                                           auth_url, region_name)
                            response_data = json.loads(connection.read())
                            services_list = response_data['token']['catalog']
                            endpoints_list = []
                            _url = None
                            for service in services_list:
                                service_type = service['type']
                                service_name = service['name']
                                if service_type == "volume" and service_name == "cinder":
                                    endpoints_list = service['endpoints']
                                    break
                            for endpoint in endpoints_list:
                                interface = endpoint['interface']
                                region_id = endpoint['region_id']
                                if region_name:
                                    if interface == "public" and region_id == region_name:
                                        _url = endpoint['url']
                                        break
                                else:
                                    if len(endpoints_list) == 3:
                                        _url = endpoint['url']
                                        break
                            token = connection.info().getheader('X-Subject-Token')
                            url_list = _url.split(":")
                            auth_url_list = auth_url.split(":")
                            url_list[1] = auth_url_list[1]
                            url = ":".join(url_list) + "/types?is_public=None"
                            req = urllib2.Request(url)
                            req.get_method = lambda: 'GET'
                            req.add_header("content-type", "application/json")
                            req.add_header("X-Auth-Token", token)
                            resp = urllib2.urlopen(req)
                            volume_type_list = json.loads(resp.read())
                            volume_type_list = volume_type_list['volume_types']
                            i = 60
                        except:
                            i = i + 1
                            time.sleep(i)
                    return volume_type_list, token, ":".join(url_list)

                type_list, token, url = _get_volume_type_list()
                if volume_type not in [type['name'] for type in type_list]:
                    url = url + "/types"
                    req = urllib2.Request(url)
                    req.get_method = lambda: 'POST'
                    req.add_header("content-type", "application/json")
                    req.add_header("X-Auth-Token", token)
                    type_data = {"volume_type": {"os-volume-type-access:is_public": True, "name": volume_type, "description": None}}
                    req.add_data(json.dumps(type_data))
                    resp = urllib2.urlopen(req)
                    volume_resp = json.loads(resp.read())
                    _volume_type = volume_resp['volume_type']
                    type_id = _volume_type['id']
                    LOG.info("creating volume type = %s" % volume_type)
                    url = url + "/%s/extra_specs" % str(type_id)
                    req = urllib2.Request(url)
                    req.get_method = lambda: 'POST'
                    req.add_header("content-type", "application/json")
                    req.add_header("X-Auth-Token", token)
                    key_data = {"extra_specs": {"volume_backend_name": pool_name}}
                    req.add_data(json.dumps(key_data))
                    urllib2.urlopen(req)
                    LOG.info("Set extra specs {volume_backend_name: %s} on a volume type" % pool_name)
            else:
                def _get_volume_type_list():
                    volume_type_list = []
                    i = 0
                    while i < 60:
                        try:
                            cinderclient = cc.Client(
                                username,
                                password,
                                tenant_name,
                                auth_url,
                                region_name=region_name
                            )
                            volume_type_list = cinderclient.volume_types.list()
                            i = 60
                        except:
                            i = i + 1
                            time.sleep(i)
                    return volume_type_list

                if volume_type not in [type.name for type in _get_volume_type_list()]:
                    cinderclient = cc.Client(
                        username,
                        password,
                        tenant_name,
                        auth_url,
                        region_name=region_name
                    )
                    cinder = cinderclient.volume_types.create(volume_type)
                    LOG.info("creating volume type = %s" % volume_type)
                    cinder.set_keys({"volume_backend_name": pool_name})
                    LOG.info("Set extra specs {volume_backend_name: %s} on a volume type" % pool_name)


    def _create_osd_state(self, context, strg, osd_id):
        osd_state = {}
        osd_state['osd_name'] = 'osd.%d' % osd_id
        osd_state['device_id'] = strg['dev_id']
        osd_state['storage_group_id'] = strg['storage_group_id']
        osd_state['service_id'] = strg['service_id']
        osd_state['cluster_id'] = strg['cluster_id']
        osd_state['state'] = FLAGS.osd_in_up
        osd_state['operation_status'] = FLAGS.vsm_status_present
        osd_state['weight'] = 1.0
        osd_state['public_ip'] = strg['secondary_public_ip']
        osd_state['cluster_ip'] = strg['cluster_ip']
        osd_state['deleted'] = 0
        osd_state['weight'] = 1.0
        osd_state['operation_status'] = FLAGS.vsm_status_present
        osd_state['zone_id'] = strg['zone_id']
        LOG.info('ADD_OSD _create_osd_state %s' % osd_state)
        self._conductor_rpcapi.osd_state_create(context, osd_state)

    def _remove_osd_state(self, context, id):
        osd_name = 'osd.%s' % id
        val = { 'osd_name': osd_name, 'deleted': 1 }
        self._conductor_rpcapi.osd_state_update_or_create(context,
            val, create=False)

    def get_ceph_config(self, context):
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf).as_dict()
        LOG.info("ceph config %s" % config)
        return config

    def save_ceph_config(self, context, config):
        """
        config: dict
        """
        config = cephconfigparser.CephConfigParser(config)
        #with open(FLAGS.ceph_conf, 'w') as ceph_conf:
        config.save_conf(FLAGS.ceph_conf)
        return True

    def inital_ceph_osd_db_conf(self, context, server_list, file_system, ceph_conf_in_cluster_manifest=None):
        config = cephconfigparser.CephConfigParser()
        osd_num = db.device_get_count(context)
        LOG.info("osd_num:%d" % osd_num)
        settings = db.vsm_settings_get_all(context)
        for setting in settings:
            if setting['name'] == 'ceph_near_full_threshold':
                cnfth = setting['value']
            elif setting['name'] == 'ceph_full_threshold':
                cfth = setting['value']
            elif setting['name'] == 'pg_count_factor':
                pg_count_factor = int(setting['value'])
            elif setting['name'] == 'heartbeat_interval':
                heartbeat_interval = setting['value']
            elif setting['name'] == 'osd_heartbeat_interval':
                osd_heartbeat_interval = setting['value']
            elif setting['name'] == 'osd_heartbeat_grace':
                osd_heartbeat_grace = setting['value']
            elif setting['name'] == 'osd_pool_default_size':
                pool_default_size = setting['value']

        global_kvs = {'heartbeat_interval':heartbeat_interval,
                      'osd_heartbeat_interval':osd_heartbeat_interval,
                      'osd_heartbeat_grace':osd_heartbeat_grace,
                      'pool_default_size':pool_default_size,
                      }

        if ceph_conf_in_cluster_manifest:
            for cell in ceph_conf_in_cluster_manifest:
                if not cell['name'].startswith('osd_') and not cell['name'].startswith('mon_'):
                    global_kvs[cell['name']] = cell['default_value']

        config.add_global(global_kvs)

        is_first_mon = True
        is_first_osd = True
        mon_cnt = -1
        osd_cnt = -1

        for host in server_list:
            #DEBUG for debug here.
            LOG.info(' host list: %s' % host)
            if host['is_monitor']:
                mon_cnt = mon_cnt + 1
                monitor = db.init_node_get_by_id(context, host['id'])
                hostname = monitor['host']
                hostip = monitor['secondary_public_ip']
                if is_first_mon:
                    # config.add_mds_header()
                    #config.add_mds(hostname, hostip, '0')
                    #values = {'mds': 'yes'}
                    #db.init_node_update(context, host['id'], values)
                    mon_header_kvs = {
                        'cnfth':cnfth,
                        'cfth':cfth,
                    }
                    if ceph_conf_in_cluster_manifest:
                        for cell in ceph_conf_in_cluster_manifest:
                            if cell['name'].startswith('mon_'):
                                global_kvs[cell['name']] = cell['default_value']

                    config.add_mon_header(mon_header_kvs)
                    is_first_mon = False
                    config.add_mon(hostname, hostip, mon_cnt)
                else:
                    config.add_mon(hostname, hostip, mon_cnt)

            if host['is_storage']:
                # Get disks list info from DB.
                strgs = self._conductor_rpcapi.\
                    host_storage_groups_devices(context,
                                                host['id'])

                LOG.info('strg list: %s' % strgs)
                if strgs and is_first_osd:
                    fs_type = strgs[0]['file_system']
                    osd_heartbeat_interval= db.vsm_settings_get_by_name(context,'osd_heartbeat_interval').get('value')
                    osd_heartbeat_grace= db.vsm_settings_get_by_name(context,'osd_heartbeat_grace').get('value')
                    # validate fs type
                    if fs_type in ['xfs', 'ext3', 'ext4', 'btrfs']:
                        #config.add_osd_header(osd_type=fs_type)
                        osd_header_kvs = {
                            'osd_type':fs_type,
                            'osd_heartbeat_interval':osd_heartbeat_interval,
                            'osd_heartbeat_grace':osd_heartbeat_grace,

                        }
                        if ceph_conf_in_cluster_manifest:
                            for cell in ceph_conf_in_cluster_manifest:
                                if cell['name'].startswith('osd_'):
                                    osd_header_kvs[cell['name']] = cell['default_value']
                        config.add_osd_header(osd_header_kvs)
                    else:
                        config.add_osd_header()
                    is_first_osd = False
                for strg in strgs:
                    # NOTE: osd_cnt stands for the osd_id.
                    osd_cnt = osd_cnt + 1
                    LOG.info(' strg = %s' % \
                            (json.dumps(strg, sort_keys=True, indent=4)))

                    config.add_osd(strg['host'],
                                   strg['secondary_public_ip'],
                                   strg['cluster_ip'],
                                   strg['dev_name'],
                                   strg['dev_journal'],
                                   osd_cnt)

                    self._create_osd_state(context,
                                           strg,
                                           osd_cnt)
                    mount_point = '%sosd%s' % \
                        (FLAGS.osd_data_path, osd_cnt)
                    utils.ensure_tree(mount_point)

                    val = {}
                    val['id'] = strg['dev_id']
                    val['mount_point'] = mount_point
                    val['fs_type'] = file_system
                    LOG.info('device_update values = %s, osd_id = %s' % \
                         (val, osd_cnt))
                    self._conductor_api.device_update(context, val['id'], val)

        config.save_conf(FLAGS.ceph_conf)

    def mkcephfs(self):
        LOG.info('mkcephfs in agent/driver.py')
        utils.execute('mkcephfs',
                      '-a',
                      '-c', FLAGS.ceph_conf,
                      '-k', FLAGS.keyring_admin,
                      # '--mkfs',
                      run_as_root=True)
        LOG.info('mkcephfs over in agent/driver.py')
        return True

    def start_ceph(self, context):
        utils.execute('service', 'ceph', '-a', 'start', run_as_root=True)
        return True

    def _stop_all_ceph_service(self):
        run_path = '/var/run/ceph/'
        try:
            pids = utils.execute('ls', run_path, run_as_root=True)[0]
            for pid_file in pids.split():
                try:
                    LOG.info('KILL %s' % pid_file)
                    if pid_file.find('pid') != -1:
                        self._kill_by_pid_file(run_path + pid_file)
                except:
                    LOG.info('KILL PROCESS')

            pids = utils.execute('pgrep', 'ceph', run_as_root=True)[0]
            for pid in pids.split():
                try:
                    LOG.info('KILL pid = %s' % pid)
                    utils.execute('kill', '-9',
                                  pid,
                                  ignore_exit_code=True,
                                  run_as_root=True)
                except:
                    LOG.info('KILL BY PGREP')
        except:
            LOG.info('Stop meet error')
            ceph_version = self.get_ceph_version()
            if int(ceph_version.split(".")[0]) > 0:
                LOG.info("ceph version is greater than hammer, ceph user exists")
                LOG.info("Create /var/lib/ceph directory, and chown ceph:ceph")
                utils.execute('mkdir', '-p', run_path, run_as_root=True)
                utils.execute('chown', '-R', 'ceph:ceph',
                              run_path, run_as_root=True)

    def _clean_dirs(self, dir_path):
        try:
            files = utils.execute('ls', dir_path, run_as_root=True)[0]
            files = files.split()
            for f in files:
                try:
                    utils.execute('rm', '-rf', dir_path + "/" + f,
                                        ignore_exit_code=True,
                                        run_as_root=True)
                except:
                    LOG.info('Error when delete file = %s' % f)
        except:
            LOG.info('LOOK UP dir failed %s' % dir_path)

    def _clean_ceph_conf(self):
        try:
            self._clean_dirs('/etc/ceph/')
        except:
            LOG.info('Delete files meet error!')

    def _clean_lib_ceph_files(self):
        # delete dirty files in mds.
        try:
            osd_list = utils.execute('ls', '/var/lib/ceph/osd/',
                                     ignore_exit_code=True,
                                     run_as_root=True)[0]
            LOG.info('Get osd_list = %s' % osd_list)
            for osd in osd_list.split():
                try:
                    LOG.info('Begin to umount %s' % osd)
                    self._clean_dirs('/var/lib/ceph/osd/%s' % osd)
                    utils.execute('umount', '/var/lib/ceph/osd/' + osd,
                                  ignore_exit_code = True,
                                  run_as_root=True)
                except:
                    LOG.info('umount /var/lib/ceph/osd/%s' % osd)
            self._clean_dirs('/var/lib/ceph/')
        except:
            LOG.info('rm  monitor files error')

    def _build_lib_ceph_dirs(self):
        try:
            dirs_list = ['bootstrap-mds', 'bootstrap-osd',
                         'mds', 'mon', 'osd', 'tmp']
            for d in dirs_list:
                utils.execute('mkdir', '-p', '/var/lib/ceph/' + d,
                              run_as_root=True)
            ceph_version = self.get_ceph_version()
            if int(ceph_version.split(".")[0]) > 0:
                utils.execute('chown', '-R',
                              'ceph:ceph',
                              '/var/lib/ceph',
                              run_as_root=True)
        except:
            LOG.info('build dirs in /var/lib/ceph failed!')

    def __format_devs(self, context, disks, file_system):
        # format devices to xfs.
        def ___fdisk(disk):
            cluster = db.cluster_get_all(context)[0]
            mkfs_option = cluster['mkfs_option']
            if not mkfs_option:
                mkfs_option = utils.get_fs_options(file_system)[0]
            utils.execute('mkfs.%s' % file_system,
                          mkfs_option,
                          disk,
                          run_as_root=True)

        thd_list = []
        for disk in disks:
            thd = utils.MultiThread(___fdisk, disk=disk)
            thd_list.append(thd)

        try:
            utils.start_threads(thd_list)
        except:
            pass

    def clean_ceph_data(self, context, osd_disks, journal_disks, file_system):
        utils.execute('chown', '-R', 'vsm:vsm', '/var/lib/ceph/',
                        run_as_root=True)
        self._stop_all_ceph_service()
        self._stop_all_ceph_service()
        time.sleep(1)
        self._clean_ceph_conf()
        self._clean_lib_ceph_files()
        self._build_lib_ceph_dirs()
        self.__format_devs(context, osd_disks + journal_disks, file_system)
        return {'status': 'ok'}

    def get_dev_by_mpoint(self, directory):
        def _parse_proc_partitions():
            parts = {}
            for line in file('/proc/partitions'):
                fields = line.split()
                try:
                    dmaj = int(fields[0])
                    dmin = int(fields[1])
                    name = fields[3]
                    parts[(dmaj, dmin)] = name
                except:
                    pass
            return parts

        dev = os.stat(directory).st_dev
        major, minor = os.major(dev), os.minor(dev)
        parts = _parse_proc_partitions()
        return '/dev/' + parts[(major, minor)]

    def mount_disks(self, context, devices, fs_type):
        def __mount_disk(disk):
            utils.execute('mkdir',
                          '-p',
                          disk['mount_point'],
                          run_as_root=True)
            ceph_version = self.get_ceph_version()
            if int(ceph_version.split(".")[0]) > 0:
                utils.execute('chown', '-R',
                              'ceph:ceph',
                              disk['mount_point'],
                              run_as_root=True)
                utils.execute('chown',
                              'ceph:ceph',
                              disk['name'],
                              run_as_root=True)
                utils.execute('chown',
                              'ceph:ceph',
                              disk['journal'],
                              run_as_root=True)
            cluster = db.cluster_get_all(context)[0]
            mount_options = cluster['mount_option']
            if not mount_options:
                mount_options = utils.get_fs_options(fs_type)[1]
            utils.execute('mount',
                          '-t', fs_type,
                          '-o', mount_options,
                          disk['name'],
                          disk['mount_point'],
                          run_as_root=True)

        thd_list = []
        for dev in devices:
            thd = utils.MultiThread(__mount_disk, disk=dev)
            thd_list.append(thd)
        utils.start_threads(thd_list)

    def is_new_storage_group(self, storage_group):
        nodes = self.get_crushmap_nodes()
        for node in nodes:
            if storage_group == node['name']:
                return False
        return True

    def is_new_zone(self, zone):
        nodes = self.get_crushmap_nodes()
        for node in nodes:
            if zone == node['name']:
                return False
        return True

    def get_ceph_osd_info(self):
        '''
        Locally execute 'ceph osd dump -f json' and return the json block as a python data structure.
        :return: a python data structure containing the json content returned by 'ceph osd dump -f json'
        '''
        output = utils.execute("ceph", "osd", "dump", "-f", "json", run_as_root=True)[0]
        return json.loads(output)

    def get_ceph_disk_list(self):
        '''
        Execute 'sudo ceph-disk list' and gather ceph partition info.
        :return: a python data structure containing the content of 'sudo ceph-disk list'
        '''
        output = utils.execute('ceph-disk', 'list', run_as_root=True)[0]
        return self.v09_ceph_disk_list_parser(output) if 'ceph data' in output\
          else self.v08_ceph_disk_list_parser(output)

    def v09_ceph_disk_list_parser(self, output):
        '''
        Parse the output of 'ceph-disk list' as if we're running against a v0.9 ceph (infernalis) or higher.
        :param output: the output to be parsed.
        :return: a list of disk-info dictionaries.
        '''
        disk_list = []
        for line in output.split('\n'):
            if 'ceph data' in line:
                # /dev/sdb1 ceph data, active, cluster ceph, osd.0, journal /dev/sdb2
                disk_dict = {}
                parts = line.strip().split(', ')
                disk_dict[u'dev'] = parts[0].split()[0]
                disk_dict[u'state'] = parts[1]
                disk_dict[u'cluster'] = parts[2].split()[-1]
                disk_dict[u'id'] = int(parts[3].split('.')[-1])
                disk_dict[u'journal'] = parts[4].split()[-1]
                disk_list.append(disk_dict)
        return disk_list

    def v08_ceph_disk_list_parser(self, output):
        '''
        Parse the output of 'ceph-disk list' as if we're running against a v0.8 ceph (firefly) or lower.
        :param output: the output to be parsed.
        :return: a list of disk-info dictionaries.
        '''
        disk_list = []
        for line in output.split('\n'):
            if '/osd/' in line:
                # /dev/sdb4 other, xfs, mounted on /var/lib/ceph/osd/osd0
                disk_dict = {}
                parts = line.strip().split(', ')
                osd_path = parts[-1].split()[-1]
                osd_id = self.get_osd_whoami(osd_path)
                osd_daemon_cfg = self.get_osd_daemon_map(osd_id, 'config')
                osd_daemon_status = self.get_osd_daemon_map(osd_id, 'status')
                disk_dict[u'dev'] = parts[0].split()[0]
                disk_dict[u'state'] = osd_daemon_status['state']
                disk_dict[u'cluster'] = osd_daemon_cfg['cluster']
                disk_dict[u'id'] = osd_id
                disk_dict[u'journal'] = osd_daemon_cfg['osd_journal']
                disk_list.append(disk_dict)
        return disk_list

    def get_osd_whoami(self, osd_path):
        '''
        Return the osd id number for the osd on the specified path.
        :param osd_path: the device path of the osd - e.g., /var/lib/ceph/osd...
        :return: an integer value representing the osd id number for the target osd.
        '''
        output = utils.execute('cat', osd_path+'/whoami', run_as_root=True)[0]
        return int(output)

    def get_osd_daemon_map(self, oid, reqtype):
        '''
        command: ceph daemon osd.{oid} config show
        output: { "cluster": "ceph",
                  ...
                  "osd_journal": "\/dev\/sdc1"}
        :param oid: the id number of the osd for which to obtain a journal device path.
        :param reqtype: the type of request - 'config' or 'status' (could be expanded to other types later).
        :return: a dictionary containing configuration parameters and values for the specified osd.
        '''
        values = {}
        arglist = ['ceph', 'daemon', 'osd.'+str(oid)]
        arglist.extend(['config', 'show'] if reqtype == 'config' else ['status'])
        output = utils.execute(*arglist, run_as_root=True)[0]
        for line in output.split('\n'):
            if len(line.strip()) > 1:
                attr, val = tuple(line.translate(None, ' {"\},').split(':', 1))
                values[attr] = val
        return values

    def add_osd(self, context, host_id, osd_id_in=None):

        if osd_id_in is not None:
            osd_obj = db.osd_get(context, osd_id_in)
            host_obj =  db.init_node_get_by_device_id(context, osd_obj.device_id)
            host_id = host_obj.id
            LOG.info("begin to add osd %s from host %s"%(osd_obj.device_id,host_id))

        LOG.info('start to ceph osd on %s' % host_id)
        strg_list = self._conductor_api.\
            host_storage_groups_devices(context, host_id)
        LOG.info('strg_list %s' % strg_list)

        #added_to_crushmap = False
        osd_cnt = len(strg_list)
        if osd_id_in is not None:
            osd_cnt = 1
        count = 0

        for strg in strg_list:
            if osd_id_in is not None and strg.get("dev_id") != osd_obj.device_id:
                continue
            LOG.info('>> Step 1: start to ceph osd %s' % strg)
            count = count + 1
            if osd_id_in is  None:
                self._conductor_api.init_node_update(context, host_id, {"status": "add_osd %s/%s"%(count,osd_cnt)})
            # Create osd from # ceph osd create
            stdout = utils.execute("ceph",
                                   "osd",
                                   "create",
                                   run_as_root=True)[0]

            osd_id = str(int(stdout))
            LOG.info('   gen osd_id success: %s' % osd_id)

            # step 1 end
            host = strg['host']
            zone = strg['zone']

            #TODO strg['storage_group']
            # stands for the storage_group_name fetch from DB.
            if strg.get('storage_group',None) is None:
                default_storage_group = db.storage_group_get_all(context)[0]
                strg['storage_group'] = default_storage_group['name']
                strg['storage_group_id'] = default_storage_group['id']
            storage_group = strg['storage_group']
            crush_dict = {"root": "vsm",
                          "storage_group": storage_group,
                          "zone": "_".join([zone, storage_group]),
                          "host": "_".join([host, storage_group, zone]),}

            osd_conf_dict = {"host": host,
                             "primary_public_ip": strg['primary_public_ip'],
                             "secondary_public_ip": strg['secondary_public_ip'],
                             "cluster_ip": strg['cluster_ip'],
                             "dev_name": strg['dev_name'],
                             "dev_journal": strg['dev_journal'],
                             "file_system": strg['file_system']}
            osd_state = {}
            osd_state['osd_name'] = 'osd.%s' % osd_id
            osd_state['device_id'] = strg['dev_id']
            osd_state['storage_group_id'] = strg['storage_group_id']
            osd_state['service_id'] = strg['service_id']
            osd_state['cluster_id'] = strg['cluster_id']
            osd_state['state'] = FLAGS.osd_in_up
            osd_state['weight'] = 1.0
            osd_state['operation_status'] = FLAGS.vsm_status_present
            osd_state['public_ip'] = strg['secondary_public_ip']
            osd_state['cluster_ip'] = strg['cluster_ip']
            osd_state['deleted'] = 0
            osd_state['zone_id'] = strg['zone_id']
            if osd_id_in is not None:
                osd_state_ref = db.osd_state_update(context,osd_id_in,osd_state)
            else:
                osd_state_ref = self._conductor_api.osd_state_create(context, osd_state)
            osd_state['osd_location'] = osd_state_ref['osd_location']
            osd_state['weight'] = osd_state_ref['weight'] and float(osd_state_ref['weight']) or 1.0
            LOG.info('>> crush_dict  %s' % crush_dict)
            LOG.info('>> osd_conf_dict %s' % osd_conf_dict)
            LOG.info('>> osd_state %s' % osd_state)
            values = {}
            #if not added_to_crushmap:
            #    LOG.info('>> add crushmap ')
            crushmap = self.get_crushmap_json_format()
            types = crushmap.get_all_types()
            types.sort(key=operator.itemgetter('type_id'))
            if self.is_new_storage_group(crush_dict['storage_group']):
                self._crushmap_mgmt.add_storage_group(crush_dict['storage_group'],\
                                                  crush_dict['root'],types=types)
                # zones = db.zone_get_all_not_in_crush(context)
                # for item in zones:
                #     zone_item = item['name'] + '_' + crush_dict['storage_group']
                #     self._crushmap_mgmt.add_zone(zone_item, \
                #                                 crush_dict['storage_group'],types=types)
                #
                if zone == FLAGS.default_zone:
                    self._crushmap_mgmt.add_rule(crush_dict['storage_group'], 'host')
                else:
                    self._crushmap_mgmt.add_rule(crush_dict['storage_group'], 'zone')

                #TODO update rule_id and status in DB
                rule_dict = self.get_crush_rule_dump_by_name(crush_dict['storage_group']) 
                LOG.info("rule_dict:%s" % rule_dict)
                values['rule_id'] = rule_dict['rule_id']

            if self.is_new_zone(crush_dict['zone']):
                self._crushmap_mgmt.add_zone(crush_dict['zone'], \
                                             crush_dict['storage_group'], types=types)
            self._crushmap_mgmt.add_host(crush_dict['host'],
                                         crush_dict['zone'], types=types)
            #    added_to_crushmap = True

            #There must be at least 3 hosts in every storage group when the status is "IN"
            zones, hosts = self._conductor_rpcapi.zones_hosts_get_by_storage_group(context, \
                                                        crush_dict['storage_group'])
            #LOG.info("storage group:%s" % crush_dict['storage_group'])
            #LOG.info("zones:%s" % zones)
            #LOG.info("hosts:%s" % hosts)
            #no zone and zone version
            if zones:
                if zones[0] == FLAGS.default_zone:
                    if host not in hosts and len(hosts) >= 2:
                        values['status'] = FLAGS.storage_group_in 
                else:
                    if zone not in zones and len(zones) >= 2:
                        values['status'] = FLAGS.storage_group_in 

            if values:
                db.storage_group_update_by_name(context, crush_dict['storage_group'], values)

            # other steps
            LOG.info('>> _add_osd start ')
            self._add_osd(context,
                          osd_id,
                          crush_dict,
                          osd_conf_dict,
                          osd_state)
            try:
                self.run_add_disk_hook(context)
            except:
                LOG.info('run add_disk error')

        return True

    def _add_osd(self,
                 context,
                 osd_id,
                 crush_dict,
                 osd_conf_dict,
                 osd_state,
                 weight="1.0"):

        # step 2
        LOG.info('>>> step2 start')
        #osd_pth = '%sceph-%s' % (FLAGS.osd_data_path, osd_id)
        #osd_keyring_pth = "%s/keyring" % osd_pth
        #osd_pth = '/var/lib/ceph/osd/osd%s' % osd_id
        #osd_keyring_pth = '/etc/ceph/keyring.osd.%s' % osd_id
        osd_data_path = self.get_ceph_config(context)['osd']['osd data']
        osd_pth = osd_data_path.replace('$id',osd_id)
        LOG.info('osd add osd_pth =%s'%osd_pth)
        osd_keyring_pth = self.get_ceph_config(context)['osd']['keyring']
        osd_keyring_pth = osd_keyring_pth.replace('$id',osd_id).replace('$name','osd.%s'%osd_id)
        LOG.info('osd add keyring path=%s'%osd_keyring_pth)
        utils.ensure_tree(osd_pth)

        # step 3
        LOG.info('>>> step3 start')
        # get cluster file system to format the disk
        utils.execute("umount",
                      osd_conf_dict['dev_name'],
                      check_exit_code=False,
                      run_as_root=True)

        LOG.debug("The file system is %s" % osd_conf_dict['file_system'])
        file_system = 'xfs'
        if osd_conf_dict['file_system']:
            file_system = osd_conf_dict['file_system']

        cluster = db.cluster_get_all(context)[0]
        mkfs_option = cluster['mkfs_option']
        if not mkfs_option:
            mkfs_option = utils.get_fs_options(file_system)[0]
        utils.execute("mkfs",
                      "-t", file_system,
                      mkfs_option, osd_conf_dict['dev_name'],
                      run_as_root=True)

        # TODO: does not support ext4 for now.
        # Need to use -o user_xattr for ext4
        mount_option = cluster['mount_option']
        if not mount_option:
            mount_option = utils.get_fs_options(file_system)[1]

        ceph_version = self.get_ceph_version()
        if int(ceph_version.split(".")[0]) > 0:
            utils.execute('chown',
                          'ceph:ceph',
                          osd_conf_dict['dev_name'],
                          run_as_root=True)
            utils.execute('chown',
                          'ceph:ceph',
                          osd_conf_dict['dev_journal'],
                          run_as_root=True)

        utils.execute("mount",
                      "-t", file_system,
                      "-o", mount_option,
                      osd_conf_dict['dev_name'],
                      osd_pth,
                      run_as_root=True)
        self._clean_dirs(osd_pth)

        # step 3.1
        LOG.info('>>> step3.1 start')
        ret = self._add_ceph_osd_to_config(context, osd_conf_dict, osd_id)

        # step 4 add to config file before this step
        LOG.info('>>> step4 start')
        utils.execute("ceph-osd", "-i", osd_id, "--mkfs", "--mkkey",
                       run_as_root=True)

        # step 5
        LOG.info('>>> step5 start')
        utils.execute("ceph", "auth", "del", "osd.%s" % osd_id,
                        run_as_root=True)
        utils.execute("ceph", "auth", "add", "osd.%s" % osd_id,
                      "osd", "allow *", "mon", "allow rwx",
                      "-i", osd_keyring_pth,
                      run_as_root=True)

        # step 6 zone host stg
        LOG.info('>>> step6 start')
        # utils.execute("ceph", "osd", "crush", "add", "osd.%s" % osd_id, weight,
        #          "root=%s" % crush_dict['root'],
        #          "storage_group=%s" % crush_dict['storage_group'],
        #          "zone=%s" % crush_dict['zone'], "host=%s" % crush_dict['host'],
        #          run_as_root=True)

        all_osd_in_host = db.osd_state_get_by_service_id(context,osd_state['service_id'])
        other_osd_in_host = [osd['osd_name'] for osd in all_osd_in_host if osd['device_id'] != osd_state['device_id'] and osd['state'] != 'Uninitialized']
        crushmap = self.get_crushmap_json_format()
        LOG.info("osd_location_direct=======%s"%osd_state.get('osd_location'))
        osd_location_direct = osd_state.get('osd_location')
        if osd_location_direct:
            if osd_location_direct.find('=') != -1:
                osd_location_str = osd_location_direct
            else:
                osd_location_str = "%s=%s"%(crushmap._types[1]['name'],osd_location_direct)
        elif len(other_osd_in_host) > 0:
            osd_location = crushmap._get_location_by_osd_name(other_osd_in_host[0])
            osd_location_str = "%s=%s"%(osd_location['type_name'],osd_location['name'])
        else:
            osd_location = crush_dict['host']
            osd_location_str = "%s=%s"%(crushmap._types[1]['name'],osd_location)
        LOG.info("osd_location_str=======%s"%osd_location_str)
        utils.execute("ceph", "osd", "crush", "add", "osd.%s" % osd_id, weight,
                 osd_location_str,
                 run_as_root=True)
        # step 7 start osd service
        LOG.info('>>> step7 start')
        self.start_osd_daemon(context, osd_id, is_vsm_add_osd=True)
        utils.execute("ceph", "osd", "crush", "create-or-move", "osd.%s" % osd_id, weight,
           osd_location_str,
          run_as_root=True)
        #LOG.info('osd-to-db==%s'%osd_state)
        #self._conductor_api.osd_state_create(context, osd_state)
        LOG.info('>>> step7 finish')
        return True

    def _add_ceph_osd_to_config(self, context, strg, osd_id):
        LOG.info('>>>> _add_ceph_osd_to_config start')
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        ip = strg['secondary_public_ip']

        config.add_osd(strg['host'], ip, strg['cluster_ip'],
                strg['dev_name'], strg['dev_journal'], osd_id)

        LOG.info('>>>> _add_ceph_osd_to_config config %s ' % config.as_dict())
        LOG.info('>>>> _add_ceph_osd_to_config added')
        config.save_conf(FLAGS.ceph_conf)
        return True
    def get_crushmap_json_format(self,keyring=None):
        '''
        :return:
        '''
        if keyring:
            json_crushmap,err = utils.execute('ceph', 'osd', 'crush', 'dump','--keyring',keyring, run_as_root=True)
        else:
            json_crushmap,err = utils.execute('ceph', 'osd', 'crush', 'dump', run_as_root=True)
        crushmap = CrushMap(json_context=json_crushmap)
        return crushmap
    def add_monitor(self, context, host_id, mon_id, port="6789"):
        LOG.info('>> start to add mon %s on %s' % (mon_id, host_id))
        ser = self._conductor_rpcapi.init_node_get_by_id(context, host_id)
        host_ip = ser['secondary_public_ip']
        LOG.info('>> start to add mon %s' % host_ip)
        # TODO
        # step 1
        LOG.info('>> add mon step 1 ')
        try:
            mon_data_path = self.get_ceph_config(context)['mon']['mon data']
            mon_path = mon_data_path.replace('$id',mon_id)
            #LOG.info('osd restore mon_pth =%s'%mon_path)
        except:
            mon_path = os.path.join(FLAGS.monitor_data_path,"mon" + mon_id)
        utils.ensure_tree(mon_path)
        # step 2
        LOG.info('>> add mon step 2 ')
        tmp_pth = "/tmp"
        monitor_key_pth = os.path.join(tmp_pth, 'monitor_key')
        monitor_map_pth = os.path.join(tmp_pth, 'monitor_map')
        # step 3
        LOG.info('>> add mon step 3 ')
        utils.execute("ceph", "auth", "get", "mon.", "-o", monitor_key_pth,
                        run_as_root=True)
        # step 4
        LOG.info('>> add mon step 4 ')
        utils.execute("ceph", "mon", "getmap", "-o", monitor_map_pth,
                        run_as_root=True)
        # step 5
        LOG.info('>> add mon step 5 ')
        utils.execute("ceph-mon", "-i", mon_id, "--mkfs",
            "--monmap", monitor_map_pth,
            "--keyring", monitor_key_pth,
            run_as_root=True)
        ## step 6
        #LOG.info('>> add mon step 6 ')
        #host = ":".join([host_ip, port])
        #utils.execute("ceph", "mon", "add", mon_id, host, run_as_root=True)
        ## step 7
        #LOG.info('>> add mon step 7 ')
        #self._add_ceph_mon_to_config(context, ser['host'], host_ip, mon_id=mon_id)
        #utils.execute("ceph-mon", "-i", mon_id, "--public-addr", host,
        #                run_as_root=True)

        #changed by ly
        # step 6
        LOG.info('>> add mon step 6 ')
        host = ":".join([host_ip.split(',')[0], port])
        self._add_ceph_mon_to_config(context, ser['host'], host_ip, mon_id=mon_id)
        #utils.execute("ceph-mon", "-i", mon_id, "--public-addr", host,
        #                run_as_root=True)

        # step 7
        LOG.info('>> add mon step 7 ')
        # utils.execute("ceph", "mon", "add", mon_id, host, run_as_root=True)
        self.start_mon_daemon(context, mon_id)
        LOG.info('>> add mon finish %s' % mon_id)
        return True

    def remove_monitor(self, context, host_id, is_stop=False):
        LOG.info('>> start to remove ceph mon on : %s' % host_id)
        # get host_name
        node = self._conductor_rpcapi.init_node_get_by_id(context, host_id)
        host = node['host']

        # get config
        LOG.info('>> removing ceph mon')
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config_dict = config.as_dict()

        # get mon_id
        mon_id = None
        for section in config_dict:
            if section.startswith("mon."):
                if config_dict[section]['host'] == host:
                    mon_id = section.replace("mon.", "")
        if not mon_id:
            LOG.info('>> removing ceph mon not found')
            return True

        # step 1
        LOG.info('>> removing ceph mon %s' % mon_id)
        try:
            # test ssh service in case the server is down
            LOG.info('>>>> removing ceph mon step 1: test server start!')
            utils.execute('ssh', '-q', 'root@' + host, 'exit', run_as_root=True)
        except exception.ProcessExecutionError as e:
            LOG.info('>> removing ceph mon test server error!')
            code = e.exit_code
            LOG.info('return code: %s' % code)
            if code == 0:
                # utils.execute("service",
                #               "ceph",
                #               "-a",
                #               "stop",
                #               "mon.%s" % mon_id,
                #               run_as_root=True)
                self._operate_ceph_daemon("stop", "mon", id=mon_id, ssh=True, host=host)
            # If can not ssh to that server,
            # We assume that the server has been shutdown.
            # Go steps below.

        # step 2
        LOG.info('>> removing ceph mon step 2')
        # fix the issue of ceph jewel version when remove the monitor,
        # it will throw the Error EINVAL, but the monitor remove successfully.
        try:
            utils.execute("ceph",
                          "mon",
                          "remove",
                          mon_id,
                          run_as_root=True)
        except:
            LOG.warn("Ceph throws out an error, but monitor has been remove successfully")
            pass
        if not is_stop:
            config.remove_mon(mon_id)
        # step 3
        LOG.info('>> removing ceph mon step 3')
        LOG.info('>> removing ceph mon step 4:stop  mon service ')
        try:
            self._operate_ceph_daemon("stop", "mon", id=mon_id, ssh=True, host=host)
        except:
            pass
        LOG.info('>> removing ceph mon success!')
        config.save_conf(FLAGS.ceph_conf)
        return True

        # TODO  don't remove any code from this line to the end of func
        # remove monitors from unhealthy cluster
        # step 1
        # try:
        #     utils.execute("service", "ceph", "stop", "mon", run_as_root=True)
        # except:
        #     utils.execute("stop", "ceph-mon-all", run_as_root=True)
        #self._operate_ceph_daemon("stop", "mon", id=mon_id, ssh=True, host=host)
        # step 2
        LOG.info('>> remove ceph mon step2 start')
        tmp_pth = "/tmp"
        monitor_map_pth = os.path.join(tmp_pth, 'monitor_map')
        utils.execute("ceph-mon", "-i", mon_id, "--extract-monmap",
                        monitor_map_pth, run_as_root=True)
        utils.execute("ceph-mon", "-i", "a", "--extract-monmap",
                        monitor_map_pth, run_as_root=True)
        # step 3
        LOG.info('>> remove ceph mon step3 start')
        utils.execute("monmaptool", monitor_map_pth, "--rm", mon_id,
                        run_as_root=True)
        # step 4
        LOG.info('>> remove ceph mon step4 start')
        utils.execute("ceph-mon", "-i", mon_id, "--inject-monmap",
                        monitor_map_pth, run_as_root=True)
        return True

    def remove_mds(self, context, host_id):
        """Remove mds service on host_id server."""
        def __is_host_running(host):
            try:
                self._agent_rpcapi.test_service(context,
                                                FLAGS.agent_topic,
                                                host)
                return True
            except rpc_exc.Timeout, rpc_exc.RemoteError:
                return False

        def __config_dict():
            config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
            cdict = config.as_dict()
            return cdict

        def __config_remove_mds(mds_id):
            config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
            config.remove_mds_header()
            config.remove_mds(mds_id)
            config.save_conf(FLAGS.ceph_conf)

        LOG.info('>> remove ceph mds on hostid(%s) start' % host_id)
        node = self._conductor_rpcapi.init_node_get_by_id(context, host_id)
        values = {'mds': 'no'}
        self._conductor_rpcapi.init_node_update(context, host_id, values)
        host = node['host']
        host_is_running = __is_host_running(host)
        LOG.info('host_is_running===mds==%s'%host_is_running)
        if host_is_running:
            try:
                self._agent_rpcapi.stop_mds(context, host)
            except rpc_exc.Timeout, rpc_exc.RemoteError:
                host_is_running = False
        mds_id = self.get_mds_id(host)
        if not mds_id:
            LOG.info('Have not find mds on %s' % host_id)
            return

        __config_remove_mds(mds_id)
        try:
            utils.execute('ceph', 'mds',
                          'rm', mds_id, 'mds.%s' % mds_id,'--keyring',FLAGS.keyring_admin,
                          run_as_root=True)
        except:
            pass
        try:
            utils.execute('ceph', 'auth', 'del',
                          'mds.%s' % mds_id,'--keyring',FLAGS.keyring_admin,
                          run_as_root=True)
        except:
            pass
        try:
            utils.execute('ceph', 'mds', 'newfs', '0', '1',
                          '--yes-i-really-mean-it','--keyring',FLAGS.keyring_admin,
                          run_as_root=True)
        except:
            pass
        LOG.info('remove mds success!')

    def remove_osd(self, context, host_id):
        def __is_host_running(host):
            try:
                self._agent_rpcapi.test_service(context,
                                                FLAGS.agent_topic,
                                                host)
                return True
            except rpc_exc.Timeout, rpc_exc.RemoteError:
                return False

        def __config_dict():
            config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
            cdict = config.as_dict()
            return cdict

        def __config_remove_osd(osd_id):
            config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
            config.remove_osd(osd_id)
            config.save_conf(FLAGS.ceph_conf)

        LOG.info('>> remove ceph osds on hostid(%s) start' % host_id)
        node = self._conductor_rpcapi.init_node_get_by_id(context, host_id)
        host = node['host']
        host_is_running = __is_host_running(host)
        LOG.info('host_is_running===osd==%s'%host_is_running)
        # get config
        config_dict = __config_dict()

        # get osd_ids
        osd_id_list = []
        for section in config_dict:
            if section.startswith("osd."):
                if config_dict[section]['host'] == host:
                    osd_id_list.append(section.replace("osd.", ""))
        LOG.info('>> remove ceph osd osd_ids %s' % osd_id_list)

        for osd_id in osd_id_list:
            self._remove_osd(context, osd_id, host, host_is_running)
            # step 5
            LOG.info('>>> remove ceph osd step5 osd_id %s' % osd_id)
            osd_name = 'osd.%s' % osd_id
            val = { 'osd_name': osd_name, 'deleted': 1 }
            self._conductor_rpcapi.osd_state_update(context, val)
            LOG.info('>>> remove ceph osd step 1-5 osd_id %s' % osd_id)

        #step 6
        # LOG.info('>>> Begin to remove crushmap')
        # osd_tree = utils.execute('ceph', 'osd', 'tree', run_as_root=True)[0]
        # LOG.info('>>> Get ceph osd tree = %s' % osd_tree)
        # for line in osd_tree.split('\n'):
        #     if line.lower().find(host.lower()) != -1:
        #         for x in line.split(' '):
        #             if x.lower().find(host.lower()) != -1:
        #                 utils.execute('ceph', 'osd', 'crush', 'rm', x)

        LOG.info('>>> remove ceph osd finish.')

        if not host_is_running:
            val = {'deleted': 1}
            self._conductor_rpcapi.init_node_update(context, host_id, val)
        return True

    def _add_ceph_mon_to_config(self, context, host, host_ip, mon_id):
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config.add_mon(host, host_ip, mon_id=mon_id)
        config.save_conf(FLAGS.ceph_conf)
        return True

    def _kill_by_pid_file(self, pid_file):
        # Kill process by pid file.
        # mainly for ceph.
        file_path = pid_file
        # no using os.path.exists(), because if the file is owned by ceph
        # user, the result will return false
        try:
            out, err = utils.execute('ls', file_path, run_as_root=True)
        except:
            out = ""
        # if os.path.exists(file_path):
        if out:
            # no permission to read if the file is owned by ceph user
            # pid = open(file_path).read().strip()

            out, err = utils.execute('cat', file_path, run_as_root=True)
            pid = out.strip()
            pid_live = os.path.exists('/proc/%s' % pid)
            utils.execute('rm', '-rf', file_path, run_as_root=True)
            try_times = 1
            while pid_live:
                try_times = try_times + 1

                try:
                    if try_times % 2:
                        utils.execute('kill', '-9', pid, run_as_root=True)
                    else:
                        utils.execute('kill', '-9', pid, run_as_root=True)
                except:
                    LOG.info('Seems can not stop this OSD process.')
                time.sleep(2)
                pid_live = os.path.exists('/proc/%s' % pid)
                if try_times > 100:
                    break
        return True

    def stop_osd_daemon(self, context, num):
        # stop ceph-osd daemon on the storage node
        # Param: the osd id
        # return Bool
        file_path = '/var/run/ceph/osd.%s.pid' % num
        # no using os.path.exists(), because if the file is owned by ceph
        # user, the result will return false
        try:
            out, err = utils.execute('ls', file_path, run_as_root=True)
        except:
            out = ""
        # if os.path.exists(file_path):
        if out:
            self._kill_by_pid_file(file_path)
        else:
            LOG.info("Not found pid file for osd.%s" % num)
            try:
                LOG.info("Try to stop osd %s daemon by ceph or ceph-osd command" % num)
                self._operate_ceph_daemon("stop", "osd", id=num)
            except:
                LOG.warn("Osd %s has NOT been stopped" % num)
        return True

    def start_osd_daemon(self, context, num, is_vsm_add_osd=False):
        osd = "osd.%s" % num
        LOG.info('begin to start osd = %s' % osd)
        if is_vsm_add_osd:
            ceph_version = self.get_ceph_version()
            if int(ceph_version.split(".")[0]) > 0:
                utils.execute('chown', '-R', 'ceph:ceph',
                              '/var/lib/ceph', run_as_root=True)
                utils.execute('chown', '-R', 'ceph:ceph',
                              '/etc/ceph', run_as_root=True)
            #utils.execute('service', 'ceph', 'start', osd, run_as_root=True)
        #else:
        self._operate_ceph_daemon("start", "osd", id=num)
        return True

    def stop_mon_daemon(self, context, name):
        file_path = '/var/run/ceph/mon.%s.pid' % name
        # no using os.path.exists(), because if the file is owned by ceph
        # user, the result will return false
        try:
            out, err = utils.execute('ls', file_path, run_as_root=True)
        except:
            out = ""
        # if os.path.exists(file_path):
        if out:
            self._kill_by_pid_file(file_path)
        else:
            LOG.info("Not found pid file for mon.%s" % name)
            try:
                LOG.info("Try to stop mon %s daemon by ceph or ceph-mon command" % name)
                self._operate_ceph_daemon("stop", "mon", id=name)
            except:
                LOG.warn("Mon %s has NOT been stopped" % name)
        return True

    def start_mon_daemon(self, context, name):
        try:
            self.stop_mon_daemon(context, name)
        except:
            pass
        # mon_name = 'mon.%s' % num
        # utils.execute('service', 'ceph', 'start', mon_name, run_as_root=True)
        try:
            self._operate_ceph_daemon("start", "mon", id=name)
        except:
            LOG.warn("Monitor has NOT been started!")
        return True

    def stop_mds_daemon(self, context, num):
        file_path = '/var/run/ceph/mds.%s.pid' % num
        if os.path.exists(file_path):
            self._kill_by_pid_file(file_path)
        else:
            LOG.info('Not found pid file for mds.%s' % num)
            try:
                LOG.info("Try to stop mds %s daemon by ceph or ceph-mds command" % num)
                self._operate_ceph_daemon("stop", "mds", id=num)
            except:
                LOG.warn("Mds %s has NOT been stopped" % num)
        return True

    def get_mds_id(self, host=FLAGS.host):
        """Stop mds service on this host."""
        def __config_dict():
            config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
            cdict = config.as_dict()
            return cdict
        config_dict = __config_dict()
        # get osd_ids
        mds_id = None
        for section in config_dict:
            if section.startswith("mds."):
                if config_dict[section]['host'] == host:
                    mds_id = section.replace("mds.", "")
        return mds_id

    def stop_mds(self, context):
        mds_id = self.get_mds_id()
        if mds_id:
            self.stop_mds_daemon(context, mds_id)

    def start_mds_daemon(self, context, num):
        mds_name = 'mds.%s' % num
        # utils.execute('service', 'ceph', 'start', mds_name, run_as_root=True)
        self._operate_ceph_daemon("start", "mds", id=num)

    def _get_ceph_mon_map(self):
        output = utils.execute("ceph", "mon", "dump", "-f", "json", run_as_root=True)[0]
        return json.loads(output)

    def start_monitor(self, context):
        # Get info from db.
        res = self._conductor_rpcapi.init_node_get_by_host(context, FLAGS.host)
        node_type = res.get('type', None)
        # get mon_id
        mon_id = None
        monmap = self._get_ceph_mon_map()
        mons = monmap['mons']
        for mon in mons:
            if mon['name'] == FLAGS.host:
                mon_id = mon['name']

        # Try to start monitor service.
        if mon_id:
            LOG.info('>> start the monitor id: %s' % mon_id)
            if node_type and node_type.find('monitor') != -1:
                self.start_mon_daemon(context, mon_id)

    def stop_monitor(self, context):
        # Get info from db.
        res = self._conductor_rpcapi.init_node_get_by_host(context, FLAGS.host)
        node_type = res.get('type', None)
        # get mon_id
        mon_id = None
        monmap = self._get_ceph_mon_map()
        mons = monmap['mons']
        for mon in mons:
            if mon['name'] == FLAGS.host:
                mon_id = mon['name']

        # Try to stop monitor service.
        if mon_id:
            LOG.info('>> stop the monitor id: %s' % mon_id)
            if node_type and node_type.find('monitor') != -1:
                self.stop_mon_daemon(context, mon_id)

    def start_osd(self, context):
        # Start all the osds on this node.
        osd_list = []
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config_dict = config.as_dict()

        for section in config_dict:
            if section.startswith("osd."):
                if config_dict[section]['host'] == FLAGS.host:
                    osd_id = section.replace("osd.", "")
                    osd_list.append(osd_id)

        LOG.info('osd_list = %s' % osd_list)

        def __start_osd(osd_id):
            utils.execute('start_osd', osd_id, run_as_root=True)

        thd_list = []
        for osd_id in osd_list:
            thd = utils.MultiThread(__start_osd, osd_id=osd_id)
            thd_list.append(thd)
        utils.start_threads(thd_list)

    def add_mds(self, context):
        LOG.info('add_mds')
        mds_id = self.get_mds_id()
        if mds_id:
            LOG.info('add_mds find mds on this node. Just start it.')
            self.start_mds(context)
            return

        # Change /etc/ceph.conf file.
        # Add new mds service.
        LOG.info('add_mds begin to create new mds.')
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config.add_mds_header()
        mds_id = config.get_mds_num()
        LOG.info('create new mds_id = %s' % mds_id)
        init_node_ref = db.init_node_get_by_host(context, FLAGS.host)
        hostip = init_node_ref['secondary_public_ip']
        config.add_mds(FLAGS.host, hostip, mds_id)
        config.save_conf()

        values = {'mds': 'yes'}
        db.init_node_update(context, init_node_ref['id'], values)

        # Generate new keyring.
        mds_path = '/var/lib/ceph/mds/ceph-%s' % mds_id
        utils.execute('mkdir', '-p', mds_path, run_as_root=True)
        mds_key = '/etc/ceph/keyring.mds.%s' % mds_id
        out = utils.execute('ceph', 'auth',
                      'get-or-create', 'mds.%d' % mds_id,
                      'mds', "allow",
                      'osd', "allow *",
                      'mon', "allow rwx",
                      run_as_root=True)[0]
        utils.write_file_as_root(mds_key, out, 'w')
        ceph_version = self.get_ceph_version()
        if int(ceph_version.split(".")[0]) > 0:
            utils.execute('chown', '-R',
                          'ceph:ceph',
                          '/var/lib/ceph',
                          run_as_root=True)

        # Start mds service.
        self.start_mds(context)

    def start_mds(self, context):
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        config_dict = config.as_dict()
        # mds_id
        mds_id = None
        for section in config_dict:
            if section.startswith("mds."):
                if config_dict[section]['host'] == FLAGS.host:
                    mds_id = section.replace("mds.", "")

        # Try to start monitor service.
        if mds_id:
            LOG.info('>> start the mds id: %s' % mds_id)
            try:
                self._operate_ceph_daemon("start", "mds", id=mds_id)
                # utils.execute('ceph-mds', '-i', mds_id, run_as_root=True)
            except:
                LOG.info('Meets some error on start mds service.')

    def start_server(self, context, node_id):
        """ Start server.
            0. start monitor
            1. start mds.
            2. start all osd.
            3. unset osd noout.
            4. reset db server status.
        """
        res = self._conductor_rpcapi.init_node_get_by_id(context, node_id)
        service_id = res.get('service_id', None)
        node_type = res.get('type', None)
        host_ip = res.get('secondary_public_ip', None)
        host = res.get('host', None)
        LOG.debug('The server info: %s %s %s %s' %
                  (service_id, node_type, host_ip, host))

        # start monitor
        self.start_monitor(context)

        # start mds
        self.start_mds(context)

        # get osd list; if there aren't any, update status and return
        osd_states = self._conductor_rpcapi.osd_state_get_by_service_id(context, service_id)
        if not len(osd_states) > 0:
            LOG.info("There is no osd on node %s" % node_id)
            self._conductor_rpcapi.init_node_update_status_by_id(context, node_id, 'Active')
            return True

        # async method to start an osd
        def __start_osd(osd_id):
            osd = db.get_zone_hostname_storagegroup_by_osd_id(context, osd_id)[0]
            osd_name = osd['osd_name'].split('.')[-1]
            self.start_osd_daemon(context, osd_name)
            # utils.execute("ceph", "osd", "crush", "create-or-move", osd['osd_name'], osd['weight'],
            #     "host=%s_%s_%s" %(osd['service']['host'],osd['storage_group']['name'],osd['zone']['name']) ,
            #     run_as_root=True)
            values = {'state': FLAGS.osd_in_up, 'osd_name': osd['osd_name']}
            self._conductor_rpcapi.osd_state_update_or_create(context, values)

        # start osds asynchronously
        thd_list = []
        for item in osd_states:
            osd_id = item['id']
            thd = utils.MultiThread(__start_osd, osd_id=osd_id)
            thd_list.append(thd)
        utils.start_threads(thd_list)

        # update init node status
        ret = self._conductor_rpcapi.init_node_update_status_by_id(context, node_id, 'Active')

        count = db.init_node_count_by_status(context, 'Stopped')
        if count == 0:
            utils.execute('ceph', 'osd', 'unset', 'noout', run_as_root=True)
        return True

    def track_monitors(self, mon_id):
        """Return the status of monitor in quorum."""
        # ceph --cluster=ceph \
        #      --admin-daemon \
        #      /var/run/ceph/ceph-mon.%id.asok \
        #        mon_status
        out = utils.execute('ceph',
                            '--cluster=ceph',
                            '--admin-daemon',
                            '/var/run/ceph/ceph-mon.%s.asok' % mon_id,
                            'mon_status',
                            run_as_root=True)[0]
        return json.loads(out)

    def create_keyring(self, mon_id):
        """Create keyring file:
            ceph.client.admin.keyring
            bootstrap-osd/keyring
            bootstrap-mds/keyrong
        """
        # Firstly begin to create ceph.client.admin.keyring
        utils.execute('ceph',
                      '--cluster=ceph',
                      '--name=mon.',
                      '--keyring=/var/lib/ceph/mon/mon{mon_id}/keyring'.format(
                          mon_id=mon_id,
                          ),
                      'auth',
                      'get-or-create',
                      'client.admin',
                      'mon', 'allow *',
                      'osd', 'allow *',
                      'mds', 'allow',
                      '-o',
                      '/etc/ceph/keyring.admin',
                      run_as_root=True)

        # Begin to create bootstrap keyrings.
        utils.execute('mkdir',
                      '-p',
                      '/var/lib/ceph/bootstrap-osd',
                      run_as_root=True)

        utils.execute('ceph',
                      '--cluster=ceph',
                      'auth',
                      'get-or-create',
                      'client.bootstrap-osd',
                      'mon',
                      'allow profile bootstrap-osd',
                      '-o',
                      '/var/lib/ceph/bootstrap-osd/ceph.keyring',
                      run_as_root=True)

        # Begin to create bootstrap-mds
        utils.execute('mkdir',
                      '-p',
                      '/var/lib/ceph/bootstrap-mds',
                      run_as_root=True)

        utils.execute('ceph',
                      '--cluster=ceph',
                      'auth',
                      'get-or-create',
                      'client.bootstrap-mds',
                      'mon',
                      'allow profile bootstrap-mds',
                      '-o',
                      '/var/lib/ceph/bootstrap-mds/ceph.keyring',
                      run_as_root=True)
        if self._is_systemctl():
            utils.execute('chown', '-R',
                          'ceph:ceph',
                          '/var/lib/ceph',
                          run_as_root=True)

    def stop_cluster(self,context):
        "stop cluster"
        LOG.info('agent/driver.py stop cluster')
        utils.execute('service', 'ceph', '-a', 'stop', run_as_root=True)
        return True


    def start_cluster(self,context):
        LOG.info('agent/driver.py start cluster')
        utils.execute('service', 'ceph', '-a', 'start', run_as_root=True)
        return True


    def stop_server(self, context, node_id):
        """Stop server.
           0. Remove monitor if it is a monitor
           1. Get service_id by node_id
           2. Get all osds for given service_id
           3. Set osd noout
           4. service ceph stop osd.$num
        """
        LOG.info('agent/driver.py stop_server')
        cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        LOG.info('Step 1. Scan the osds in db.')
        res = self._conductor_rpcapi.init_node_get_by_id(context, node_id)
        service_id = res.get('service_id', None)
        osd_states = self._conductor_rpcapi.\
                osd_state_get_by_service_id(context, service_id)
        if not len(osd_states) > 0:
            LOG.info("There is no osd on node %s; skipping osd shutdown." % node_id)
        else:
            LOG.info('Step 2. ceph osd set noout')
            utils.execute('ceph', 'osd', 'set', 'noout', run_as_root=True)
            for item in osd_states:
                osd_name = item['osd_name']
                LOG.info('>> Stop ceph %s' % osd_name)
                # utils.execute('service', 'ceph', 'stop', osd_name,
                #                 run_as_root=True)
                self.stop_osd_daemon(context, osd_name.split(".")[1])
                # self._operate_ceph_daemon("stop", "osd", id=osd_name.split(".")[1])
                values = {'state': 'In-Down', 'osd_name': osd_name}
                LOG.info('>> update status into db %s' % osd_name)
                self._conductor_rpcapi.osd_state_update_or_create(context, values)

        # Stop monitor service.
        self.stop_monitor(context)

        # Stop mds service.
        self.stop_mds(context)
        #We really dont' want to remove mds, right? Just stop it.
        #values = {'mds': 'no'}
        #self._conductor_rpcapi.init_node_update(context, node_id, values)

        self._conductor_rpcapi.init_node_update_status_by_id(context, node_id, 'Stopped')
        return True

    def ceph_upgrade(self, context, node_id, key_url, pkg_url,restart=True):
        """ceph_upgrade
        """
        LOG.info('agent/driver.py ceph_upgrade')
        err = 'success'
        try:
            out, err = utils.execute('vsm-ceph-upgrade',
                             run_as_root=True)
            LOG.info("exec vsm-ceph-upgrade:%s--%s"%(out,err))
            if restart:
                self.stop_server(context, node_id)
                self.start_server(context, node_id)
            err = 'success'
        except:
            LOG.info("vsm-ceph-upgrade error:%s"%err)
            err = 'error'
        db.init_node_update_status_by_id(context, node_id, 'Ceph Upgrade:%s'%err)
        pre_status = 'available'
        if restart:
            pre_status = 'Active'
        ceph_ver = self.get_ceph_version()
        LOG.info('get version--after ceph upgrade==%s'%ceph_ver)
        db.init_node_update(context,node_id,{'ceph_ver':ceph_ver})
        db.init_node_update_status_by_id(context, node_id, pre_status)
        return ceph_ver

    def get_ceph_health(self, context):
        out, err = utils.execute('ceph',
                                 'health',
                                 run_as_root=True)
        if not 'HEALTH_OK' in out and not 'HEALTH_WARN' in out:
            LOG.info('Failed to start ceph cluster: %s' % out)
            try:
                raise exception.StartCephFaild
            except exception.StartCephFaild, e:
                LOG.error("%s:%s" %(e.code, e.message))
            return True
        return True

    def get_ceph_version(self):
        try:
            out, err = utils.execute('ceph',
                                     '--version',
                                     run_as_root=True)
            out = out.split(' ')[2]
        except:
            out = ''
        return out

    def get_vsm_version(self):
        try:
            out, err = utils.execute('vsm',
                                     '--version',
                                     run_as_root=True)
        except:
            out = '2.0'
        return out

    def find_attr_start_line(self, lines, min_line=4, max_line=9):
        """
        Return line number of the first real attribute and value.
        The first line is 0.  If the 'ATTRIBUTE_NAME' header is not
        found, return the index after max_line.
        """
        for idx, line in enumerate(lines[min_line:max_line]):
            col = line.split()
            if len(col) > 1 and col[1] == 'ATTRIBUTE_NAME':
                return idx + min_line + 1

        LOG.warn('ATTRIBUTE_NAME not found in second column of'
                      ' smartctl output between lines %d and %d.'
                      % (min_line, max_line))

        return max_line + 1

    def parse_nvme_output(self, attributes, start_offset=0, end_offset=-1):
        import string

        att_list = attributes.split('\n')
        att_list = att_list[start_offset:end_offset]
        dev_info={}
        for att in att_list:
            att_kv = att.split(':')
            if not att_kv[0]: continue
            if len(att_kv) > 1:
                dev_info[string.strip(att_kv[0])] = string.strip(att_kv[1])
            else:
                dev_info[string.strip(att_kv[0])] = ''

        return dev_info

    def get_nvme_smart_info(self, device):
        smart_info_dict = {'basic':{},'smart':{}}

        if "/dev/nvme" in device:
            LOG.info("This is a nvme device : " + device)
            dev_info = {}
            dev_smart_log = {}
            dev_smart_add_log = {}

            import commands

            # get nvme device meta data
            attributes, err =  utils.execute('nvme', 'id-ctrl', device, run_as_root=True)
            if not err:
                basic_info_dict = self.parse_nvme_output(attributes)
                LOG.info("basic_info_dict=" + str(basic_info_dict))
                smart_info_dict['basic']['Drive Family'] = basic_info_dict.get('mn') or ''
                smart_info_dict['basic']['Serial Number'] = basic_info_dict.get('sn') or ''
                smart_info_dict['basic']['Firmware Version'] = basic_info_dict.get('fr') or ''
                smart_info_dict['basic']['Drive Status'] = 'PASSED'
            else:
                smart_info_dict['basic']['Drive Status'] = 'WARN'
                LOG.warn("Fail to get device identification with error: " + str(err))

            # get nvme devic smart data
            attributes, err = utils.execute('nvme', 'smart-log', device, run_as_root=True)
            if not err:
                dev_smart_log_dict = self.parse_nvme_output(attributes, 1)
                LOG.info("device smart log=" + str(dev_smart_log_dict))
                for key in dev_smart_log_dict:
                    smart_info_dict['smart'][key] = dev_smart_log_dict[key]
            else:
                smart_info_dict['basic']['Drive Status'] = 'WARN'
                LOG.warn("Fail to get device smart log with error: " + str(err))

            # get nvme device smart additional data
            attributes, err = utils.execute('nvme', 'smart-log-add', device, run_as_root=True)
            if not err:
                dev_smart_log_add_dict = self.parse_nvme_output(attributes, 2)
                LOG.info("device additional smart log=" + str(dev_smart_log_add_dict))
                smart_info_dict['smart']['<<< additional smart log'] = ' >>>'
                for key in dev_smart_log_add_dict:
                    smart_info_dict['smart'][key] = dev_smart_log_add_dict[key]
            else:
                smart_info_dict['basic']['Drive Status'] = 'WARN'
                LOG.warn("Fail to get device additional (vendor specific) smart log with error: "  + str(err))

        LOG.info(smart_info_dict)
        return smart_info_dict

    def get_smart_info(self, context, device):
        LOG.info('retrieve device info for ' + str(device))
        if "/dev/nvme" in device:
            return self.get_nvme_smart_info(device)

        attributes, err = utils.execute('smartctl', '-A', device, run_as_root=True)
        attributes = attributes.split('\n')
        start_line = self.find_attr_start_line(attributes)
        smart_info_dict = {'basic':{},'smart':{}}
        if start_line < 10:
            for attr in attributes[start_line:]:
                attribute = attr.split()
                if len(attribute) > 1 and attribute[1] != "Unknown_Attribute":
                    smart_info_dict['smart'][attribute[1]] = attribute[9]


        basic_info, err = utils.execute('smartctl', '-i', device, run_as_root=True)
        basic_info = basic_info.split('\n')
        basic_info_dict = {}
        if len(basic_info)>=5:
            for info in basic_info[4:]:
                info_list = info.split(':')
                if len(info_list) == 2:
                    basic_info_dict[info_list[0]] = info_list[1]
        smart_info_dict['basic']['Drive Family'] = basic_info_dict.get('Device Model') or basic_info_dict.get('Vendor') or ''
        smart_info_dict['basic']['Serial Number'] = basic_info_dict.get('Serial Number') or ''
        smart_info_dict['basic']['Firmware Version'] = basic_info_dict.get('Firmware Version') or ''

        status_info,err = utils.execute('smartctl', '-H', device, run_as_root=True)
        status_info = status_info.split('\n')
        smart_info_dict['basic']['Drive Status'] = ''
        if len(status_info)>4:
            status_list = status_info[4].split(':')
            if len(status_list)== 2:
                smart_info_dict['basic']['Drive Status'] = len(status_list[1]) < 10 and status_list[1] or ''
        LOG.info("get_smart_info_dict:%s"%(smart_info_dict))
        return smart_info_dict

    def get_available_disks(self, context):
        all_disk_info,err = utils.execute('blockdev','--report',run_as_root=True)
        all_disk_info = all_disk_info.split('\n')
        all_disk_name = []
        disk_check = []
        if len(all_disk_info)>1:
            for line in all_disk_info[1:-1]:
                LOG.info('line====%s'%line)
                line_list = line.split(' ')
                line_list.remove('')
                LOG.info('line_list====%s'%line_list)
                if int(line_list[-4]) <= 1024:
                    continue
                if line_list[-1].find('-') != -1:
                    continue
                if line_list[-9] and int(line_list[-9]) == 0:
                    disk_check.append(line_list[-1])
                all_disk_name.append(line_list[-1])
        for disk_check_cell in disk_check:
            for disk in all_disk_name:
                if disk != disk_check_cell and disk.find(disk_check_cell) == 0:
                    all_disk_name.remove(disk_check_cell)
                    break
        mounted_disk_info,err = utils.execute('mount', '-l', run_as_root=True)
        mounted_disk_info = mounted_disk_info.split('\n')
        for mounted_disk in mounted_disk_info:
            mounted_disk_list = mounted_disk.split(' ')
            if mounted_disk_list[0].find('/dev/') != -1:
                if mounted_disk_list[0] in all_disk_name:
                    all_disk_name.remove(mounted_disk_list[0])
        pvs_disk_info,err = utils.execute('pvs', '--rows', run_as_root=True)
        pvs_disk_info = pvs_disk_info.split('\n')
        for line in pvs_disk_info:
            line_list = line.split(' ')
            if line_list[-1].find('/dev/') != -1 and line_list[-1] in all_disk_name:
                all_disk_name.remove(line_list[-1])

        return all_disk_name


    def get_disks_name(self, context,disk_bypath_list):
        disk_name_dict = {}
        for bypath in disk_bypath_list:
            out, err = utils.execute('ls',bypath,'-l',
                         run_as_root=True)
            if len(out.split('../../'))>1:
                disk_name_dict[bypath] = '/dev/%s'%(out.split('../../')[1][:-1])
        return disk_name_dict

    def get_disks_name_by_path_dict(self,disk_name_list):
        disk_name_dict = {}
        by_path_info,err = utils.execute('ls','-al','/dev/disk/by-path',run_as_root=True)
        LOG.info('by_path_info===%s,err===%s'%(by_path_info,err))
        for bypath in by_path_info.split('\n'):
            bypath_list = bypath.split(' -> ../../')
            if len(bypath_list) > 1:
                disk_name_dict['/dev/%s'%(bypath_list[1])] = '/dev/disk/by-path/%s'%(bypath_list[0].split(' ')[-1])
        return disk_name_dict

    def get_disks_name_by_uuid_dict(self,disk_name_list):
        disk_name_dict = {}
        by_uuid_info,err = utils.execute('ls','-al','/dev/disk/by-uuid',run_as_root=True)
        LOG.info('by_uuid_info===%s,err===%s'%(by_uuid_info,err))
        for byuuid in by_uuid_info.split('\n'):
            byuuid_list = byuuid.split(' -> ../../')
            if len(byuuid_list) > 1:
                disk_name_dict['/dev/%s'%(byuuid_list[1])] = '/dev/disk/by-path/%s'%(byuuid_list[0].split(' ')[-1])
        return disk_name_dict

    def run_add_disk_hook(self, context):
        out, err = utils.execute('add_disk',
                                 'll',
                                 run_as_root=True)
        LOG.info("run_add_disk_hook:%s--%s"%(out,err))
        return out

    def get_ceph_admin_keyring(self, context):
        """
        read ceph keyring from CEPH_PATH
        """
        with open(FLAGS.keyring_admin, "r") as fp:
            keyring_str = fp.read()
        return keyring_str

    def save_ceph_admin_keyring(self, context, keyring_str):
        """
        read ceph keyring from CEPH_PATH
        """
        open(FLAGS.keyring_admin, 'w').write(keyring_str)
        return True

    def refresh_osd_number(self, context):
        LOG.info("Start Refresh OSD number ")
        config_dict = cephconfigparser.CephConfigParser(FLAGS.ceph_conf).as_dict()
        osd_num_dict = {}

        for section in config_dict:
            if section.startswith("osd."):
                host = config_dict[section]['host']
                if not host in config_dict:
                    osd_num_dict.setdefault(host,  0)
                osd_num_dict[host] += 1
        LOG.info("Refresh OSD number %s " % osd_num_dict)

        init_nodes = self._conductor_rpcapi.get_server_list(context)
        init_node_dict = {}
        for node in init_nodes:
            init_node_dict.setdefault(node['host'], node)

        for host in osd_num_dict:
            values = {"data_drives_number": osd_num_dict[host]}
            self._conductor_rpcapi.init_node_update(context,
                                                    init_node_dict[host],
                                                    values)
        LOG.info("Refresh OSD number finish")
        return True

    def _remove_osd(self, context, osd_id, host, host_is_running=True):
        def _get_line(osd_id):
            out = utils.execute('ceph',
                                'osd',
                                'dump',
                                '-f',
                                'json-pretty',
                                run_as_root=True)[0]
            status = json.loads(out)
            for x in status['osds']:
                if int(x['osd']) == int(osd_id):
                    return x
            return None

        def _wait_osd_status(osd_id, key, value):
            status = _get_line(osd_id)
            if not status:
                time.sleep(10)
                return

            try_times = 0
            while str(status[key]) != str(value):
                try_times = try_times + 1
                if try_times > 120:
                    break

                status = _get_line(osd_id)
                if not status:
                    time.sleep(10)
                    return

                time.sleep(5)
                if try_times % 10 == 0:
                    LOG.info('Try %s: %s change key = %s to value = %s' % \
                            (try_times, osd_id, key, value))

        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)

        # Step 1: out this osd.
        LOG.info('>>> remove ceph osd osd_id %s' % osd_id)
        LOG.info('>>> remove ceph osd step0 out osd %s' % osd_id)
        utils.execute("ceph", "osd", "out", osd_id, run_as_root=True)
        LOG.info('>>> remove ceph osd step0 out osd cmd over')
        _wait_osd_status(osd_id, 'in', 0)

        # Step 2: shutdown the process.
        if host_is_running:
            LOG.info('>>> remove ceph osd kill proc osd %s' % osd_id)
            try:
                self._operate_ceph_daemon("stop", "osd", id=osd_id,
                                          ssh=True, host=host)
            except:
                utils.execute("service", "ceph", "-a", "stop", "osd.%s" % osd_id,
                              run_as_root=True)
        _wait_osd_status(osd_id, 'up', 0)

        # Step 3: Remove it from crushmap.
        LOG.info('>>> remove ceph osd step1 osd_id %s' % osd_id)
        utils.execute("ceph", "osd", "crush", "remove", "osd.%s" % osd_id,
                        run_as_root=True)

        # Step 4: Remove it from auth list.
        LOG.info('>>> remove ceph osd step2 osd_id %s' % osd_id)
        utils.execute("ceph", "auth", "del", "osd.%s" % osd_id,
                        run_as_root=True)

        # Step 5: rm it.
        LOG.info('>>> remove ceph osd step3 osd_id %s' % osd_id)
        utils.execute("ceph", "osd", "rm", osd_id, run_as_root=True)

        # Step 6: Remove it from ceph.conf
        LOG.info('>>> remove ceph osd step4 osd_id %s' % osd_id)
        config.remove_osd(osd_id)
        config.save_conf(FLAGS.ceph_conf)

    def osd_remove(self, context, osd_id, device, osd_host, umount_path):
        LOG.info('osd_remove osd_id = %s' % osd_id)
        self._remove_osd(context, osd_id, osd_host)
        utils.execute("umount",
                      umount_path,
                      check_exit_code=False,
                      run_as_root=True)
        return True

    def ceph_osd_stop(self, context, osd_name):
        # utils.execute('service',
        #               'ceph',
        #               '-a',
        #               'stop',
        #               osd_name,
        #               run_as_root=True)
        osd_id = osd_name.split('.')[-1]
        self.stop_osd_daemon(context, osd_id)
        #self._operate_ceph_daemon("stop", "osd", id=osd_name.split(".")[1],
        #                          ssh=True, host=osd_host)
        #osd_id = osd_name.split('.')[-1]
        #values = {'state': 'Out-Down', 'osd_name': osd_name}
        #ret = self._conductor_rpcapi.\
        #        osd_state_update_or_create(context, values)

    def ceph_osd_start(self, context, osd_name):
        osd_id = osd_name.split('.')[-1]
        self.start_osd_daemon(context, osd_id)
        #values = {'state': FLAGS.osd_in_up, 'osd_name': osd_name}
        #ret = self._conductor_rpcapi.\
        #        osd_state_update_or_create(context, values)

    def osd_restart(self, context, osd_id):
        LOG.info('osd_restart osd_id = %s' % osd_id)
        osd = db.get_zone_hostname_storagegroup_by_osd_id(context, osd_id)
        osd=osd[0]
        #stop
        utils.execute('ceph', 'osd', 'set', 'noout', run_as_root=True)
        self.ceph_osd_stop(context, osd['osd_name'])
        #start
        utils.execute('ceph', 'osd', 'unset', 'noout', run_as_root=True)
        self.ceph_osd_start(context, osd['osd_name'])
        time.sleep(10)
        # utils.execute("ceph", "osd", "crush", "create-or-move", osd['osd_name'], osd['weight'],
        #   "host=%s_%s_%s" %(osd['service']['host'],osd['storage_group']['name'],osd['zone']['name']) ,
        #  run_as_root=True)
        return True

    def osd_restore(self, context, osd_id):
        LOG.info('osd_restore osd_id = %s' % osd_id)
        osd = db.osd_get(context, osd_id)
        init_node = db.init_node_get_by_service_id(context, osd['service_id'])
        osd_conf_dict = {"host": FLAGS.host,
                        "primary_public_ip": init_node['primary_public_ip'],
                        "secondary_public_ip": init_node['secondary_public_ip'],
                        "cluster_ip": init_node['cluster_ip'],
                        "dev_name": osd['device']['name'],
                        "dev_journal": osd['device']['journal'],
                        "file_system": osd['device']['fs_type']}
        LOG.debug('osd_conf_dict = %s' % osd_conf_dict)
        stdout = utils.execute("ceph",
                               "osd",
                               "create",
                               run_as_root=True)[0]

        osd_inner_id = str(int(stdout))
        osd_name = 'osd.%s' % osd_inner_id

        LOG.info("new osd_name = %s" % osd_name)

        utils.execute("umount",
                      osd['device']['name'],
                      check_exit_code=False,
                      run_as_root=True)

        file_system = 'xfs'
        if osd['device']['fs_type']:
            file_system = osd['device']['fs_type']

        cluster = db.cluster_get_all(context)[0]
        mkfs_option = cluster['mkfs_option']
        if not mkfs_option:
            mkfs_option = utils.get_fs_options(file_system)[0]
        utils.execute("mkfs",
                      "-t", file_system,
                      mkfs_option,
                      osd['device']['name'],
                      run_as_root=True)

        #osd_pth = '%sceph-%s' % (FLAGS.osd_data_path, osd_inner_id)
        osd_data_path = self.get_ceph_config(context)['osd']['osd data']
        osd_pth = osd_data_path.replace('$id',osd_inner_id)
        LOG.info('osd restore osd_pth =%s'%osd_pth)
        utils.ensure_tree(osd_pth)
        cluster = db.cluster_get_all(context)[0]
        mount_option = cluster['mount_option']
        if not mount_option:
            mount_option = utils.get_fs_options(file_system)[1]
        utils.execute("mount",
                      "-t", file_system,
                      "-o", mount_option,
                      osd['device']['name'],
                      osd_pth,
                      run_as_root=True)

        self._clean_dirs(osd_pth)

        self._add_ceph_osd_to_config(context, osd_conf_dict, osd_inner_id)
        utils.execute("ceph-osd",
                      "-i", osd_inner_id,
                      "--mkfs",
                      "--mkkey",
                      run_as_root=True)

        utils.execute("ceph", "auth", "del", "osd.%s" % osd_inner_id,
                        run_as_root=True)
        osd_keyring_pth = self.get_ceph_config(context)['osd']['keyring']
        osd_keyring_pth = osd_keyring_pth.replace('$id',osd_inner_id).replace('$name','osd.%s'%osd_inner_id)
        LOG.info('osd restore keyring path=%s'%osd_keyring_pth)
        #osd_keyring_pth = "/etc/ceph/keyring.osd.%s" % osd_inner_id
        utils.execute("ceph", "auth", "add", "osd.%s" % osd_inner_id,
                      "osd", "allow *", "mon", "allow rwx",
                      "-i", osd_keyring_pth,
                      run_as_root=True)

        storage_group = osd['storage_group']['name']

        #TODO change zone
        if osd['osd_location']:
            osd_location_str = ''
            if osd['osd_location'].find('=') != -1:
                osd_location_str = osd['osd_location']
            else:
                crushmap = self.get_crushmap_json_format()
                osd_location_str = "%s=%s"%(crushmap._types[1]['name'],osd['osd_location'])
            weight = "1.0"
            utils.execute("ceph",
                      "osd",
                      "crush",
                      "add",
                      "osd.%s" % osd_inner_id,
                      weight,
                      osd_location_str,
                      run_as_root=True)
        else:
            zone = init_node['zone']['name']
            crush_dict = {"root": 'vsm',
                        "storage_group":storage_group,
                        "zone": "_".join([zone, storage_group]),
                        "host": "_".join([FLAGS.host, storage_group, zone]),
                        }
            weight = "1.0"
            utils.execute("ceph",
                          "osd",
                          "crush",
                          "add",
                          "osd.%s" % osd_inner_id,
                          weight,
                          "root=%s" % crush_dict['root'],
                          "storage_group=%s" % crush_dict['storage_group'],
                          "zone=%s" % crush_dict['zone'],
                          "host=%s" % crush_dict['host'],
                          run_as_root=True)

        #step1
        self.start_osd_daemon(context, osd_inner_id)
        #step2
        utils.execute('ceph', 'osd', 'in', osd_name, run_as_root=True)
        time.sleep(10)
        # utils.execute("ceph", "osd", "crush", "create-or-move", "osd.%s" % osd_inner_id, weight,
        #   "host=%s" % crush_dict['host'],
        #  run_as_root=True)
        #update db
        value = {}
        value['id'] = osd_id
        value['osd_name'] = osd_name
        value['operation_status'] = FLAGS.vsm_status_present
        value['state'] = FLAGS.osd_in_up
        db.osd_state_update(context, osd_id, value)
        return True

    def set_pool_pg_pgp_num(self, context, pool, pg_num, pgp_num):
        self.set_pool_pg_num(context, pool, pg_num)
        #need to wait for the last set pg_num
        time.sleep(120)
        self.set_pool_pgp_num(context, pool, pgp_num)
        
    def set_pool_pg_num(self, context, pool, pg_num):
        args= ['ceph', 'osd', 'pool', 'set', pool, 'pg_num', pg_num]
        utils.execute(*args, run_as_root=True)

    def set_pool_pgp_num(self, context, pool, pgp_num):
        args= ['ceph', 'osd', 'pool', 'set', pool, 'pgp_num', pgp_num]
        utils.execute(*args, run_as_root=True)

    def get_ec_profiles(self):
        DEFAULT_PLUGIN_PATH = "/usr/lib/ceph/erasure-code"
        args = ['ceph', 'osd', 'erasure-code-profile', 'ls']
        (out, err) = utils.execute(*args, run_as_root=True)
        profile_names = out.splitlines()
        profiles = []
        for profile_name in profile_names:
            args = ['ceph', 'osd', 'erasure-code-profile', 'get', profile_name]
            (out, err) = utils.execute(*args, run_as_root=True)
            profile = {}
            profile['name'] = profile_name
            profile['plugin_path'] = DEFAULT_PLUGIN_PATH
            profile_kv = {}
            for item in out.splitlines():
                key, val = item.split('=')
                if key == 'plugin':
                    profile['plugin'] = val
                elif key == 'directory':
                    profile['plugin_path'] = val
                else:
                    profile_kv[key] = val
            profile['pg_num'] = int(profile_kv['k']) + int(profile_kv['m'])
            profile['plugin_kv_pair'] = json.dumps(profile_kv)
            profiles.append(profile)
        return profiles

    def get_osds_status(self):
        args = ['ceph', 'osd', 'dump', '-f', 'json']
        #args = ['hostname', '-I']
        #(out, _err) = utils.execute(*args)
        (out, _err) = utils.execute(*args, run_as_root=True)
        if out != "":
            #LOG.info("osd_status:%s", out)
            return out
        else:
            return None

    def get_osds_details(self):
        args = ['ceph', 'osd', 'dump']
        osd_dump = self._run_cmd_to_json(args)
        if osd_dump:
            return osd_dump['osds']
        else:
            return None

    def get_osds_metadata(self):
        args = ['ceph', 'report']
        report = self._run_cmd_to_json(args)
        if report:
            return report['osd_metadata']
        else:
            return None

    def get_ceph_health_list(self):
        args = ['ceph', 'health']
        out, _err = utils.execute(*args, run_as_root=True)
        try:
            k = out.find(" ")
            status = out[:k]
            health_list =[i.strip() for i in out[k:].split(";")]
            return [status] + health_list
        except:
            return ["GET CEPH STATUS ERROR"]

    def make_cmd(self, args):
        h_list = list()
        t_list = ['-f', 'json-pretty']
        if isinstance(args, list):
            h_list.extend(args)
            h_list.extend(t_list)
        else:
            h_list.append(args)
            h_list.append(t_list)

        return h_list

    def _run_cmd_to_json(self, args, pretty=True):
        if pretty:
            cmd = self.make_cmd(args)
        else:
            cmd = args
        LOG.debug('command is %s' % cmd)
        (out, err) = utils.execute(*cmd, run_as_root=True)
        json_data = None
        if out:
            try:
                json_data = json.loads(out)
            except:
                json_data = None
                LOG.error('CMD result is invalid.cmd is %s.ret of cmd is %s.'%(cmd,out))
        return json_data

    def get_osds_total_num(self):
        args = ['ceph', 'osd', 'ls']
        osd_list = self._run_cmd_to_json(args)
        return len(osd_list)
 
    def get_crushmap_nodes(self):
        args = ['ceph', 'osd', 'tree']
        node_dict = self._run_cmd_to_json(args)
        node_list = []
        if node_dict:
            node_list = node_dict.get('nodes')
        return node_list

    def get_osds_tree(self):
        return_list = list()
        node_list = self.get_crushmap_nodes()
        if node_list:
            for node in node_list:
                name = node.get('name')
                id = node.get('id')
                if name and name.startswith('osd.'):
                    #LOG.debug('node %s ' % node)
                    for node_2 in node_list:
                        if node_2.get('children') and id in node_2.get('children'):
                            osd_location = '%s=%s'%(node_2.get('type'),node_2.get('name'))
                            node['osd_location'] = osd_location
                            break
                    return_list.append(node)
        #LOG.debug('osd list: %s' % return_list)
        return return_list

    def get_osd_capacity(self):
        args = ['ceph', 'pg', 'dump', 'osds']
        osd_dict = self._run_cmd_to_json(args)
        #LOG.debug('osd list: %s' % osd_dict)
        return osd_dict

    def get_pool_status(self):
        args = ['ceph', 'osd', 'dump']
        dump_list = self._run_cmd_to_json(args)
        if dump_list:
            return dump_list.get('pools')
        return None

    def get_pool_usage(self):
        args = ['ceph', 'pg', 'dump', 'pools']
        return self._run_cmd_to_json(args)

    def get_pool_stats(self):
        args = ['ceph', 'osd', 'pool', 'stats']
        return self._run_cmd_to_json(args)

    def get_osd_lspools(self):
        args = ['ceph', 'osd', 'lspools']
        pool_list = self._run_cmd_to_json(args)
        return pool_list

    def get_rbd_lsimages(self, pool):
        #args = ['rbd', 'ls', '-l', pool, \
        #       '--format', 'json', '--pretty-format']
        args = ['rbd_ls', pool] 
        rbd_image_list = self._run_cmd_to_json(args, pretty=False)
        return rbd_image_list

    def get_rbd_image_info(self, image, pool):
        args = ['rbd', '--image', \
                 image,\
                 '-p', pool, \
                 '--pretty-format',\
                 '--format', 'json', \
                 'info']
        rbd_image_dict = self._run_cmd_to_json(args, pretty=False)
        return rbd_image_dict
 
    def get_rbd_status(self):
        pool_list = self.get_osd_lspools()
        if pool_list:
            rbd_list = []
            for pool in pool_list:
                rbd_image_list = self.get_rbd_lsimages(pool['poolname'])
                if rbd_image_list:
                    for rbd_image in rbd_image_list:
                        rbd_dict = {}
                        image_dict = self.get_rbd_image_info(\
                                     rbd_image['image'], \
                                     pool['poolname'])
                        if image_dict:
                            rbd_dict['pool'] = pool['poolname']
                            rbd_dict['image'] = rbd_image['image']
                            rbd_dict['size'] = rbd_image['size']
                            rbd_dict['format'] = rbd_image['format']
                            rbd_dict['objects'] = image_dict['objects']
                            rbd_dict['order'] = image_dict['order']
                            rbd_list.append(rbd_dict)
            return rbd_list
        else:
            return None

    def get_mds_dump(self):
        args = ['ceph', 'mds', 'dump']
        mds_dict = self._run_cmd_to_json(args)
        return mds_dict

    def get_mds_status(self):
        mds_dict = self.get_mds_dump()
        if mds_dict:
            mds_list = []
            for key in mds_dict['info'].keys():
                dict = {}
                item = mds_dict['info'][key]
                dict['gid'] = item['gid']
                dict['name'] = item['name']
                dict['state'] = item['state']
                dict['address'] = item['addr']
                mds_list.append(dict)
            return mds_list
        else:
            return

    def get_pg_dump(self):
        args = ['ceph', 'pg', 'dump', 'pgs_brief']
        result = self._run_cmd_to_json(args)
        return result

    def get_pg_status(self):
        val_list = self.get_pg_dump()
        if val_list:
            pg_list = []
            for item in val_list:
                dict = {}
                dict['pgid'] = item['pgid']
                dict['state'] = item['state']
                dict['up'] = ','.join(str(v) for v in item['up'])
                dict['acting'] = ','.join(str(v) for v in item['acting'])
                pg_list.append(dict)
            return pg_list
        else:
            return

    def get_mon_health(self):
        args = ['ceph', 'health']
        return self._run_cmd_to_json(args)

    def get_ceph_status(self):
        args = ['ceph', 'status']
        return self._run_cmd_to_json(args)

    def get_crush_rule_dump_by_name(self, name):
        args = ['ceph', 'osd', 'crush', 'rule', 'dump', name]
        return self._run_cmd_to_json(args)

    def get_summary(self, sum_type, sum_dict=None):
        if sum_type in [FLAGS.summary_type_pg, FLAGS.summary_type_osd,
                        FLAGS.summary_type_mds, FLAGS.summary_type_mon,
                        FLAGS.summary_type_cluster, FLAGS.summary_type_vsm]:
            if not sum_dict:
                sum_dict = self.get_ceph_status()

            # newer versions of 'ceph status' don't display mdsmap - use 'ceph mds dump' instead
            # if not 'mdsmap' in sum_dict:
            sum_dict['mdsmap'] = self._run_cmd_to_json(['ceph', 'mds', 'dump'])

            if sum_dict:
                if sum_type == FLAGS.summary_type_pg:
                    return self._pg_summary(sum_dict)
                elif sum_type == FLAGS.summary_type_osd:
                    return self._osd_summary(sum_dict)
                elif sum_type == FLAGS.summary_type_mds:
                    return self._mds_summary(sum_dict)
                elif sum_type == FLAGS.summary_type_mon:
                    return self._mon_summary(sum_dict)
                elif sum_type == FLAGS.summary_type_cluster:
                    return self._cluster_summary(sum_dict)
                elif sum_type == FLAGS.summary_type_vsm:
                    return self._vsm_summary(sum_dict)

    def _osd_summary(self, sum_dict):
        if sum_dict:
            osdmap = sum_dict.get('osdmap')
            return json.dumps(osdmap)
        return None

    def _pg_summary(self, sum_dict):
        if sum_dict:
            pgmap = sum_dict.get('pgmap')
            return json.dumps(pgmap)
        return None

    def _mds_summary(self, sum_dict):
        if sum_dict:
            sum_dict = sum_dict.get("mdsmap")
            mdsmap = {}
            mdsmap['max'] = sum_dict['max_mds']
            mdsmap['up'] = len(sum_dict['up'])
            mdsmap['epoch'] = sum_dict['epoch']
            mdsmap['in'] = len(sum_dict['in'])
            mdsmap['failed'] = len(sum_dict['failed'])
            mdsmap['stopped'] = len(sum_dict['stopped'])
            mdsmap['data_pools'] = sum_dict['data_pools']
            mdsmap['metadata_pool'] = sum_dict['metadata_pool']
            return json.dumps(mdsmap)
        return None

    def _mon_summary(self, sum_dict):
        if sum_dict:
            quorum_status = self.get_quorum_status()
            quorum_leader_name = quorum_status.get('quorum_leader_name')
            quorum_leader_rank = None
            for mon in quorum_status.get('monmap').get('mons'):
                if mon.get('name') == quorum_leader_name:
                    quorum_leader_rank = str(mon.get('rank'))
                    break
            mon_data = {
                'monmap_epoch': sum_dict.get('monmap').get('epoch'),
                'monitors': len(sum_dict.get('monmap').get('mons')),
                'election_epoch': sum_dict.get('election_epoch'),
                'quorum': json.dumps(' '.join([str(i) for i in sum_dict.get('quorum')])).strip('"'),
                'overall_status': json.dumps(sum_dict.get('health').get('overall_status')).strip('"'),
                'quorum_leader_name':quorum_leader_name,
                'quorum_leader_rank':quorum_leader_rank,
            }
            return json.dumps(mon_data)

    def get_quorum_status(self):
        args = ['ceph', 'quorum_status']
        out = self._run_cmd_to_json(args)
        return out

    def _cluster_summary(self, sum_dict):
        if sum_dict:
            cluster_data = {
                'cluster': sum_dict.get('fsid'),
                'status': sum_dict.get('health').get('summary'),
                'detail': sum_dict.get('health').get('detail'),
                'health_list': sum_dict.get("health_list")
            }
            return json.dumps(cluster_data)

    def _vsm_summary(self, sum_dict):
        #TODO: run cmd uptime | cut -d ' ' -f2
        try:
            uptime = open("/proc/uptime", "r").read().strip().split(" ")[0]
        except:
            uptime = ""
        ceph_version = self.get_ceph_version()
        return json.dumps({
            'uptime': uptime,
            'ceph_version': ceph_version,
            'vsm_version':" ",
        })

    def ceph_status(self):
        is_active = True
        try:
            self.get_ceph_status()
        except exception.ProcessExecutionError as e:
            LOG.debug('exit_code: %s, stderr: %s' % (e.exit_code, e.stderr))
            if e.exit_code == 1 and e.stderr.find('TimeoutError') != -1:
                is_active = False
        return json.dumps({
            'is_ceph_active': is_active
        })

    def add_cache_tier(self, context, body):
        storage_pool_name = db.pool_get(context, body.get("storage_pool_id")).get('name')
        cache_pool_name = db.pool_get(context, body.get("cache_pool_id")).get('name')
        cache_mode = body.get("cache_mode")
        LOG.info("add cache tier start")
        LOG.info("storage pool %s cache pool %s " % (storage_pool_name, cache_pool_name))

        if body.get("force_nonempty"):
            utils.execute("ceph", "osd", "tier", "add", storage_pool_name, \
                      cache_pool_name, "--force-nonempty",  run_as_root=True)
        else:
            utils.execute("ceph", "osd", "tier", "add", storage_pool_name, \
                          cache_pool_name, run_as_root=True)

        # for the latest ceph version(jewel), it needs the parameter
        # --yes-i-really-mean-it to do the action.
        cache_mode_args = ["ceph",
                           "osd",
                           "tier",
                           "cache-mode",
                           cache_pool_name,
                           cache_mode]
        ceph_version_code = ceph_version_utils.get_ceph_version_code()
        if ceph_version_code == constant.CEPH_JEWEL:
            cache_mode_args.append("--yes-i-really-mean-it")
        utils.execute(*cache_mode_args, run_as_root=True)
        if cache_mode == "writeback":
            utils.execute("ceph", "osd", "tier", "set-overlay", storage_pool_name, \
                          cache_pool_name, run_as_root=True)

        db.pool_update(context, body.get("storage_pool_id"), {"cache_tier_status": "Storage pool for:%s" % cache_pool_name})
        db.pool_update(context, body.get("cache_pool_id"), {
            "cache_tier_status": "Cache pool for:%s" % storage_pool_name,
            "cache_mode": cache_mode})

        options = body.get("options")
        self._configure_cache_tier(cache_pool_name, options)
        LOG.info("add cache tier end")

        return True

    def _configure_cache_tier(self, cache_pool_name, options):
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "hit_set_type", options["hit_set_type"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "hit_set_count", options["hit_set_count"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "hit_set_period", options["hit_set_period_s"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "target_max_bytes", int(options["target_max_mem_mb"]) * 1000000, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "cache_target_dirty_ratio", options["target_dirty_ratio"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "cache_target_full_ratio", options["target_full_ratio"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "target_max_objects", options["target_max_objects"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "cache_min_flush_age", options["target_min_flush_age_m"], run_as_root=True)
        utils.execute("ceph", "osd", "pool", "set", cache_pool_name, "cache_min_evict_age", options["target_min_evict_age_m"], run_as_root=True)

    def remove_cache_tier(self, context, body):
        LOG.info("Remove Cache Tier")
        LOG.info(body)
        cache_pool = db.pool_get(context, body.get("cache_pool_id"))
        cache_pool_name = cache_pool.get("name")
        storage_pool_name = cache_pool.get("cache_tier_status").split(":")[1].strip()
        LOG.info(cache_pool['name'])
        cache_mode = cache_pool.get("cache_mode")
        LOG.info(cache_mode)
        if cache_mode == "writeback":
            # for the latest ceph version(jewel), it needs the parameter
            # --yes-i-really-mean-it to do the action.
            cache_mode_args = ["ceph",
                               "osd",
                               "tier",
                               "cache-mode",
                               cache_pool_name,
                               "forward"]
            ceph_version_code = ceph_version_utils.get_ceph_version_code()
            if ceph_version_code == constant.CEPH_JEWEL:
                cache_mode_args.append("--yes-i-really-mean-it")
            utils.execute(*cache_mode_args, run_as_root=True)
            utils.execute("rados", "-p", cache_pool_name, "cache-flush-evict-all", \
                          run_as_root=True)
            utils.execute("ceph", "osd", "tier", "remove-overlay", storage_pool_name, \
                          run_as_root=True)
        else:
            utils.execute("ceph", "osd", "tier", "cache-mode", cache_pool_name, \
                          "none", run_as_root=True)
        utils.execute("ceph", "osd", "tier", "remove", storage_pool_name, \
                      cache_pool_name, run_as_root=True)
        db.pool_update(context, cache_pool.pool_id, {"cache_tier_status": None})
        # TODO cluster id
        if body.has_key('cluster_id') and body['cluster_id']:
            cluster_id = body['cluster_id']
        else:
            cluster_id = db.cluster_get_all(context)[0]['id']
        db.pool_update_by_name(context, storage_pool_name, cluster_id, {"cache_tier_status": None})
        return True

    def auth_caps(self, context, entity, **kwargs):
        """
        update caps for <name> from caps specified in the command
        :param context:
        :param entity:
        :param kwargs:
        :return:
        """

        caps_keys = kwargs.keys()
        if "mon" in caps_keys:
            caps_mon = kwargs['mon']
        else:
            caps_mon = ""
        if "osd" in caps_keys:
            caps_osd = kwargs['osd']
        else:
            caps_osd = ""
        if "mds" in caps_keys:
            caps_mds = kwargs['mds']
        else:
            caps_mds = ""

        try:
            if caps_mon and caps_osd and caps_mds:
                utils.execute('ceph', 'auth', 'caps', entity, 'mds', caps_mds,
                              'mon', caps_mon, 'osd', caps_osd, run_as_root=True)
            elif caps_mon and caps_osd:
                utils.execute('ceph', 'auth', 'caps', entity, 'mon', caps_mon,
                              'osd', caps_osd, run_as_root=True)
            elif caps_mon:
                utils.execute('ceph', 'auth', 'caps', entity, 'mon', caps_mon,
                              run_as_root=True)
        except:
            LOG.error("Failed to update auth caps")
            raise

    def auth_get(self, context, entity):
        """
        get auth info
        :param entity: client.ce1032ba-9ae9-4a7f-b456-f80fd821dd7f
        :return:
        {
            "entity":"client.ce1032ba-9ae9-4a7f-b456-f80fd821dd7f",
            "key":"AQB7Gp9WAP+tJRAAgvZTJJqJ\/GxHEL28a4DwLQ==",
            "caps":{
                "mon":"allow r",
                "osd":"allow class-read object_prefix rbd_children,allow rwx pool=testpool01,allow rwx pool=testpool02"
            }
        }
        """

        out = utils.execute('ceph', 'auth', 'get', entity, '-f', 'plain',
                               run_as_root=True)[0].strip("\n").split("\n")
        result = {}
        result["caps"] = {}
        for line in out:
            line = line.strip(" ")
            if len(line.split("=")) < 2:
                result["entity"] = line.replace("[","").replace("]","")
            else:
                if "key" in line.split("=")[0]:
                    result["key"] = line.split("=")[1].strip()
                elif "mon" in line.split("=")[0]:
                    result["caps"]["mon"] = "=".join(line.split("=")[1:]).strip()[1:-1]
                elif "osd" in line.split("=")[0]:
                    result["caps"]["osd"] = "=".join(line.split("=")[1:]).strip()[1:-1]
                elif "mds" in line.split("=")[0]:
                    result["caps"]["mds"] = "=".join(line.split("=")[1:]).strip()[1:-1]

        return result

    def delete_cinder_type(self, context, name, **kwargs):
        """

        :param name: cinder type name
        :param kwargs:
        :return:
        """

        username = kwargs.pop('username')
        password = kwargs.pop('password')
        tenant_name = kwargs.pop('tenant_name')
        auth_url = kwargs.pop('auth_url')
        region_name = kwargs.pop('region_name')
        cinderclient = cc.Client(username,
                                 password,
                                 tenant_name,
                                 auth_url,
                                 region_name=region_name)
        cinder_type_list = cinderclient.volume_types.list()
        delete_type = None
        for type in cinder_type_list:
            if type.name == name:
                delete_type = type
                break
        if delete_type:
            cinderclient.volume_types.delete(delete_type)
        else:
            LOG.warn("Not found the cinder type %s" % name)

    def revoke_storage_pool_from_cinder_conf(self, context, auth_host,
                                             cinder_host, ssh_user,
                                             pool_name):
        """

        :param auth_host:
        :param cinder_host:
        :param ssh_user: ssh user
        :param pool_name: pool name
        :return:
        """

        line, err = utils.execute("su", "-s", "/bin/bash", "-c",
                                  "exec ssh %s ssh %s sudo sed -n '/^enabled_backends/=' /etc/cinder/cinder.conf" %
                                  (auth_host, cinder_host),
                                  ssh_user, run_as_root=True)
        line = line.strip(" ").strip("\n")
        search_str = str(line) + "p"
        enabled_backends, err = utils.execute("su", "-s", "/bin/bash", "-c",
                                              "exec ssh %s ssh %s sudo sed -n %s /etc/cinder/cinder.conf" %
                                              (auth_host, cinder_host, search_str),
                                              ssh_user, run_as_root=True)
        enabled_backends = enabled_backends.strip(" ").strip("\n")
        backends_list = enabled_backends.split("=")[1].strip(" ").split(",")
        new_backends_list = []
        for backend in backends_list:
            if backend != pool_name:
                new_backends_list.append(backend)
        new_enabled_backends = "enabled_backends\\\\\\ =\\\\\\ " + str(",".join(new_backends_list))
        utils.execute("su", "-s", "/bin/bash", "-c",
                      "exec ssh %s ssh %s sudo sed -i 's/^enabled_backends*.*/%s/g' /etc/cinder/cinder.conf" %
                      (auth_host, cinder_host, new_enabled_backends),
                      ssh_user, run_as_root=True)

        search_str = '/rbd_pool\\\\\\ =\\\\\\ ' + pool_name + '/='
        line, err = utils.execute("su", "-s", "/bin/bash", "-c",
                                  "exec ssh %s ssh %s sudo sed -n \"%s\" /etc/cinder/cinder.conf" %
                                  (auth_host, cinder_host, search_str),
                                  ssh_user, run_as_root=True)
        line = line.strip(" ").strip("\n")
        # remove 10 lines total
        start_line = int(line) - 2
        line_after = 9
        end_line = int(start_line) + line_after
        utils.execute("su", "-s", "/bin/bash", "-c",
                      "exec ssh %s ssh %s sudo sed -i %s','%s'd' /etc/cinder/cinder.conf" %
                      (auth_host, cinder_host, start_line, end_line), ssh_user,
                      run_as_root=True)
        try:
            utils.execute("service", "cinder-api", "restart", run_as_root=True)
            utils.execute("service", "cinder-volume", "restart", run_as_root=True)
            LOG.info("Restart cinder-api and cinder-volume successfully")
        except:
            utils.execute("service", "openstack-cinder-api", "restart", run_as_root=True)
            utils.execute("service", "openstack-cinder-volume", "restart", run_as_root=True)
            LOG.info("Restart openstack-cinder-api and openstack-cinder-volume successfully")

    def create_keyring_and_key_for_rgw(self, context, name, keyring):
        try:
            utils.execute("rm", keyring, run_as_root=True)
        except:
            pass
        utils.execute("ceph-authtool", "--create-keyring", keyring,
                      run_as_root=True)
        utils.execute("chmod", "+r", keyring, run_as_root=True)
        try:
            utils.execute("ceph", "auth", "del", "client." + name, run_as_root=True)
        except:
            pass
        utils.execute("ceph-authtool", keyring, "-n", "client." + name,
                      "--gen-key", run_as_root=True)
        utils.execute("ceph-authtool", "-n", "client." + name,
                      "--cap", "osd", "allow rwx", "--cap", "mon", "allow rw",
                      keyring, run_as_root=True)
        utils.execute("ceph", "-k", FLAGS.keyring_admin, "auth", "add",
                      "client." + name, "-i", keyring, run_as_root=True)

    def add_rgw_conf_into_ceph_conf(self, context, name, host, keyring,
                                    log_file, rgw_frontends):
        config = cephconfigparser.CephConfigParser(FLAGS.ceph_conf)
        rgw_section = "client." + str(name)
        config.add_rgw(rgw_section, host, keyring, log_file, rgw_frontends)
        config.save_conf(rgw=True)
        LOG.info("+++++++++++++++end add_rgw_conf_into_ceph_conf")

    def create_default_pools_for_rgw(self, context):
        utils.execute("ceph", "osd", "pool", "create", ".rgw", 8, 8, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "create", ".rgw.control", 8, 8, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "create", ".rgw.gc", 8, 8, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "create", ".log", 8, 8, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "create", ".intent-log", 8, 8, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "create", ".usage", 8, 8, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "create", ".users", 8, 8, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "create", ".users.email", 8, 8, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "create", ".users.swift", 8, 8, run_as_root=True)
        utils.execute("ceph", "osd", "pool", "create", ".users.uid", 8, 8, run_as_root=True)


class DbDriver(object):
    """Executes commands relating to TestDBs."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        pass

    def init_host(self, host):
        pass

    def update_recipe_info(self, context):
        LOG.info("DEBUG in update_recipe_info() in DbDriver()")
        res = db.recipe_get_all(context)
        recipe_id_list = []
        for x in res:
            recipe_id_list.append(int(x.recipe_id))
   
        str0 = os.popen("ssh root@10.239.82.125 \'ceph osd lspools\' ").read()
        str = str0[0:-2]
        LOG.info('DEBUG str from mon %s' % str)
        items = str.split(',')
        ##
        items.remove('5 -help')
        LOG.info("DEBUG items %s" % items)
        ## 
        pool_name_list = []
        attr_names = ['size', 'min_size', 'crash_replay_interval', 'pg_num',
                     'pgp_num', 'crush_ruleset',]
 
        for item in items:
            x = item.split()
            pool_name_list.append(x[1])
            pool_name = x[1]
            pool_id = int(x[0])
            values = {}
            values['recipe_name'] = pool_name
            for attr_name in attr_names:
                val = os.popen("ssh root@10.239.82.125 \'ceph osd pool\
                                get %s %s\'" % (pool_name, attr_name)).read()
                LOG.info("DEBUG val from cmon %s" % val)
                _list = val.split(':')
                values[attr_name] = int(_list[1])
            if pool_id in recipe_id_list:
                LOG.info('DEBUG update pool: %s recipe values %s' % (pool_name, values))
                db.recipe_update(context, pool_id, values)
            else:
                values['recipe_id'] = pool_id
                LOG.info('DEBUG create pool: %s recipe values %s' % (pool_name, values))
                db.recipe_create(context, values)

    def update_pool_info(self, context):
        LOG.info("DEBUG in update_pool_info() in DbDriver()")
        attr_names = ['size', 'min_size', 'crash_replay_interval', 'pg_num',
                     'pgp_num', 'crush_ruleset',]
        res = db.pool_get_all(context)
        pool_list = []
        for x in res:
            pool_list.append(int(x.pool_id))
            LOG.info('x.id = %s' % x.pool_id)

        #str0 = "0 data,1 metadata,2 rbd,3 testpool_after_periodic"
        str0 = os.popen("ssh root@10.239.82.125 \'ceph osd lspools\' ").read()
        str = str0[0:-2]
        items = str.split(',')
        LOG.info("DEBUG items %s pool_list %s" % (items, pool_list))
        for i in items:
            x = i.split()
            values = {}
            pool_id = int(x[0])
            LOG.info('DEBUG x[0] %s' % pool_id)
            pool_name = x[1]
            for attr_name in attr_names:
                val = os.popen("ssh root@10.239.82.125 \'ceph osd pool\
                                get %s %s\'" % (pool_name, attr_name)).read()
                LOG.info("DEBUG val from cmon %s" % val)
                _list = val.split(':')
                values[attr_name] = int(_list[1])

            if pool_id in pool_list:
                #pool_id = x[0]
                values['name'] = x[1]
                db.pool_update(context, pool_id, values)
            else:
                values['pool_id'] = pool_id
                values['name'] = x[1]
                values['recipe_id'] = pool_id
                values['status'] = 'running'
                db.pool_create(context, values)

        return res

class CreateCrushMapDriver(object):
    """Create crushmap file"""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        self.conductor_api = conductor.API()
        self.conductor_rpcapi = conductor_rpcapi.ConductorAPI()
        self.osd_num = 0
        self._crushmap_path = "/var/run/vsm/crushmap"
        fd = open(self._crushmap_path, 'w')
        fd.write("")
        fd.close()

    def _write_to_crushmap(self, string):
        fd = open(self._crushmap_path, 'a')
        fd.write(string)
        fd.close()

    def add_new_zone(self, context, zone_name):
        res = self.conductor_api.storage_group_get_all(context)
        storage_groups = []
        for i in res:
            storage_groups.append(i["name"])
        storage_groups = list(set(storage_groups))

        for storage_group in storage_groups:
            zone = zone_name + "_" + storage_group
            utils.execute("ceph", "osd", "crush", "add-bucket", zone, "zone",'--keyring',FLAGS.keyring_admin,
                            run_as_root=True)
            utils.execute("ceph", "osd", "crush", "move", zone,
                          "storage_group=%s" % storage_group,'--keyring',FLAGS.keyring_admin,
                          run_as_root=True)

        values = {'name': zone_name,
                  'deleted': 0}
        self.conductor_rpcapi.create_zone(context, values)
        return True

    def add_rule(self, name, type):
        utils.execute("ceph", "osd", "crush", "rule", "create-simple", \
                        name, name, type,'--keyring',FLAGS.keyring_admin,)
        
    def add_storage_group(self, storage_group, root, types=None):
        if types is None:
            utils.execute("ceph", "osd", "crush", "add-bucket", storage_group, \
                            "storage_group", '--keyring',FLAGS.keyring_admin,run_as_root=True)
            utils.execute("ceph", "osd", "crush", "move", storage_group,\
                            "root=%s" % root,'--keyring',FLAGS.keyring_admin, run_as_root=True)
        else:
            utils.execute("ceph", "osd", "crush", "add-bucket", storage_group, \
                            "%s"%types[3]['name'], '--keyring',FLAGS.keyring_admin,run_as_root=True)
            utils.execute("ceph", "osd", "crush", "move", storage_group,\
                            "%s=%s" %(types[-1]['name'],root),'--keyring',FLAGS.keyring_admin, run_as_root=True)

    def add_zone(self, zone, storage_group,types=None):
        if types is None:
            utils.execute("ceph", "osd", "crush", "add-bucket", zone, \
                            "zone", run_as_root=True)
            utils.execute("ceph", "osd", "crush", "move", zone, \
                            "storage_group=%s" % storage_group, run_as_root=True)
        else:
            utils.execute("ceph", "osd", "crush", "add-bucket", zone, \
                            "%s"%types[2]['name'], run_as_root=True)
            utils.execute("ceph", "osd", "crush", "move", zone, \
                            "%s=%s" %(types[3]['name'],storage_group), run_as_root=True)
    def add_host(self, host_name, zone,types=None):
        if types is None:
            utils.execute("ceph", "osd", "crush", "add-bucket", host_name, "host",'--keyring',FLAGS.keyring_admin,
                            run_as_root=True)
            utils.execute("ceph", "osd", "crush", "move", host_name,
                            "zone=%s" % zone,'--keyring',FLAGS.keyring_admin,
                            run_as_root=True)
        else:
            utils.execute("ceph", "osd", "crush", "add-bucket", host_name, "%s"%types[1]['name'],'--keyring',FLAGS.keyring_admin,
                            run_as_root=True)
            utils.execute("ceph", "osd", "crush", "move", host_name,
                            "%s=%s" %(types[2]['name'],zone),'--keyring',FLAGS.keyring_admin,
                            run_as_root=True)

    def remove_host(self, host_name):
        utils.execute("ceph", "osd", "crush", "remove", host_name,'--keyring',FLAGS.keyring_admin,
                        run_as_root=True)

    def create_crushmap(self, context, server_list):
        LOG.info("DEBUG Begin to create crushmap file in %s" % self._crushmap_path)
        LOG.info("DEBUG in create_crushmap body is %s" % server_list)
        service_id = []
        for i in server_list:
            if i["is_storage"]:
                service_id.append(i["id"])
        #service id is init node id
        LOG.info("init node id list %s" % service_id)

        osd_num = 0
        for id in service_id:
            res = self.conductor_api.osd_state_count_by_init_node_id(context, id)
            osd_num = osd_num + int(res)
        init_node = db.init_node_get(context, service_id[0])
        zone_tag = True
        zone_cnt = len(db.zone_get_all(context))
        if init_node['zone']['name'] == FLAGS.default_zone or zone_cnt <= 1:
            zone_tag = False 
        self._gen_crushmap_optimal()
        self._gen_device_osd(osd_num)
        self._gen_bucket_type()
        self._gen_bucket(context, service_id)
        self._generate_rule(context, zone_tag)
        LOG.info('Create crushmap over')
        return True

    def set_crushmap(self, context):
        LOG.info("DEBUG Begin to set crushmap")
        utils.execute('crushtool', '-c', self._crushmap_path, '-o',
                        self._crushmap_path+"_compiled", run_as_root=True)
        utils.execute('ceph', 'osd', 'setcrushmap', '-i',
                        self._crushmap_path+"_compiled", run_as_root=True)

        #the following is zone version to solve "active_remaped" etc.Don't delete it! 
        #utils.execute('crushtool', '-c', '/tmp/crushmap', 
        #                '--enable-unsafe-tunables',
        #                '--set-choose-local-tries','0',
        #                '--set-choose-local-fallback-tries', '0',
        #                '--set-choose-total-tries', '50', '-o',
        #                '/tmp/compiled_crushmap', run_as_root=True)
        #utils.execute('ceph', 'osd', 'setcrushmap', '-i',
        #                '/tmp/compiled_crushmap', run_as_root=True)
        # TODO return success here.
        return True

    def _gen_crushmap_optimal(self):
        optimal = "# begin crush map\n" \
                  "tunable choose_local_tries 0\n" \
                  "tunable choose_local_fallback_tries 0\n" \
                  "tunable choose_total_tries 50\n" \
                  "tunable chooseleaf_descend_once 1\n" \
                  "tunable chooseleaf_vary_r 1\n" \
                  "tunable straw_calc_version 1\n"
        self._write_to_crushmap(optimal)

    def _gen_device_osd(self, osd_num):
        self._write_to_crushmap("\n# devices\n")
        for i in range(0, osd_num):
            string = "device " + str(i) + " osd." + str(i) + "\n"
            self._write_to_crushmap(string)

    def _gen_bucket_type(self):
        string = "\n#types\ntype 0 osd\ntype 1 host\ntype 2 zone\
                  \ntype 3 storage_group\ntype 4 root\n\n"
        self._write_to_crushmap(string)

    def _gen_bucket(self, context, service_id):
        res = self.conductor_api.storage_group_get_all(context)
        storage_groups = []
        for i in res:
            storage_groups.append(i["name"])
        storage_groups = list(set(storage_groups))

        LOG.info("storage_groups is: %s " % storage_groups)
        res = self.conductor_api.zone_get_all(context)
        zones = []
        for i in res:
            zones.append(i["name"])

        hosts = []
        for id in service_id:
            res = self.conductor_api.init_node_get_by_id(context, id)
            hosts.append(res["host"])

        node_info = []
        LOG.info("DEB-YOU %s " % service_id)
        for id in service_id:
            res = self.conductor_api.\
                  ceph_node_info(context, id)
            for j in res:
                node_info.append(j)
        LOG.info("AGENT node info %s" % node_info)

        num = 0
        host_bucket, num = self._get_host_dic(node_info, storage_groups,\
                                             zones, service_id, num, context)
        self._write_host_bucket(host_bucket)
        zone_bucket, num = self._get_zone_dic(node_info, host_bucket,\
                                         zones, storage_groups, num)
        self._write_zone_bucket(zone_bucket)
        storage_group_bucket, num = self._get_storage_group_bucket(storage_groups,\
                                                             zone_bucket, num)
        self._write_storage_group_bucket(storage_group_bucket)
        root_bucket, num = self._get_root_bucket(storage_group_bucket, num)
        self._write_root_bucket(root_bucket)

    def _get_host_dic(self, node_info, storage_groups, zones, service_id, num, context):
        host = []
        LOG.info("service id %s " % service_id)
        for id in service_id:
            res = self.conductor_api.init_node_get_by_id(context, id)
            host_name = res["host"]
            id2 = res["zone_id"]
            res = self.conductor_api.zone_get_by_id(context, id2)
            zone = res["name"]
            for storage_group in storage_groups:
                dic = {}
                dic["name"] = host_name + "_" + storage_group + "_" + zone
                dic["zone"] = zone
                dic["storage_group"] = storage_group
                dic["id"] = num - 1
                num = num -1
                items = []
                weight = 0
                for node in node_info:
                    if node["host"] == host_name and node["storage_group_name"] == storage_group:
                        items.append(node["osd_state_name"])
                        weight = weight + 1
                dic["weight"] = (weight != 0 and weight or FLAGS.default_weight)
                dic["item"] = items
                if len(items) > 0:
                    host.append(dic)
        return host, num

    def _get_zone_dic(self, node_info, hosts, zones, storage_groups, num):
        zone_bucket = []
        for zone in zones:
            for storage_group in storage_groups:
                dic = {}
                dic["name"] = zone + "_" + storage_group
                dic["storage_group"] = storage_group
                items = []
                weight = 0
                for host in hosts:
                    if host["zone"] == zone and host["storage_group"] == storage_group:
                        item = {}
                        item["weight"] = host["weight"]
                        item["host_name"] = host["name"]
                        items.append(item)
                        weight = weight + float(host["weight"])
                dic["weight"] = (weight != 0 and weight or FLAGS.default_weight)
                dic["item"] = items
                num = num - 1
                dic["id"] = num
                if len(items) > 0:
                    zone_bucket.append(dic)
        #LOG.info('zone_bucket----%s'%zone_bucket)
        return zone_bucket, num

    def _get_storage_group_bucket(self, storage_groups, zones, num):
        storage_group_bucket = []
        for storage_group in storage_groups:
            dic = {}
            dic["name"] = storage_group
            items = []
            weight = 0
            for zone in zones:
                if zone["storage_group"] == storage_group:
                    item = {}
                    item["weight"] = zone["weight"]
                    item["zone_name"] = zone["name"]
                    items.append(item)
                    weight = weight + float(zone["weight"])
            dic["weight"] = (weight != 0 and weight or FLAGS.default_weight)
            dic["item"] = items
            num = num - 1
            dic["id"] = num
            if len(items) > 0:
                storage_group_bucket.append(dic)
        return storage_group_bucket, num

    def _get_root_bucket(self, storage_groups, num):
        root_bucket = []
        dic = {}
        dic["name"] = "vsm"
        items = []
        for storage_group in storage_groups:
            if storage_group["weight"] != 0:
                item = {}
                item["weight"] = storage_group["weight"]
                item["storage_group_name"] = storage_group["name"]
                items.append(item)
        dic["item"] = items
        num = num - 1
        dic["id"] = num
        root_bucket.append(dic)
        return root_bucket, num

    def _write_host_bucket(self, hosts):
        for host in hosts:
            self._write_to_crushmap("host " + host["name"] + " {\n")
            self._write_to_crushmap("    id " + str(host["id"]) + "\n")
            self._write_to_crushmap("    alg straw\n    hash 0\n")
            for item in host["item"]:
                self._write_to_crushmap("    item " + item + " weight 1.00\n")
            self._write_to_crushmap("}\n\n")

    def _write_zone_bucket(self, zones):
        for zone in zones:
            self._write_to_crushmap("zone " + zone["name"] + " {\n")
            self._write_to_crushmap("    id " + str(zone["id"]) + "\n")
            self._write_to_crushmap("    alg straw\n    hash 0\n")
            for item in zone["item"]:
                self._write_to_crushmap("    item " + item["host_name"] + \
                                " weight " + str(item["weight"]) + "\n")
            self._write_to_crushmap("}\n\n")

    def _write_storage_group_bucket(self, storage_groups):
        for storage_group in storage_groups:
            self._write_to_crushmap("storage_group " + storage_group["name"] + " {\n")
            self._write_to_crushmap("    id " + str(storage_group["id"]) + "\n")
            self._write_to_crushmap("    alg straw\n    hash 0\n")
            for item in storage_group["item"]:
                self._write_to_crushmap("    item " + item["zone_name"] + \
                                " weight " + str(item["weight"]) + "\n")
            self._write_to_crushmap("}\n\n")

    def _write_root_bucket(self, roots):
        for root in roots:
            self._write_to_crushmap("root " + root["name"] + " {\n")
            self._write_to_crushmap("    id " + str(root["id"]) + "\n")
            self._write_to_crushmap("    alg straw\n    hash 0\n")
            for item in root["item"]:
                self._write_to_crushmap("    item " + item["storage_group_name"] + \
                                " weight " + str(item["weight"]) + "\n")
            self._write_to_crushmap("}\n\n")

    def _key_for_sort(self, dic):
        return dic['rule_id']

    def _generate_rule(self, context, zone_tag):
        osds = self.conductor_api.osd_state_get_all(context)
        storage_groups = [ osd['storage_group']['id'] for osd in osds if osd['storage_group']]
        storage_groups = list(set(storage_groups))
        if not storage_groups :#is None:
            LOG.info("Error in getting storage_groups")
            try:
                raise exception.GetNoneError
            except exception.GetNoneError, e:
                LOG.error("%s:%s" %(e.code, e.message))
            return False
        LOG.info("DEBUG in generate rule begin")
        LOG.info("DEBUG storage_groups from conductor %s " % storage_groups)
        #sorted_storage_groups = sorted(storage_groups, key=self._key_for_sort)
        #LOG.info("DEBUG storage_groups after sorted %s" % sorted_storage_groups)
        sting_common = """    type replicated
    min_size 0
    max_size 10
"""
        if zone_tag:
            string_choose = """    step chooseleaf firstn 0 type zone
    step emit
}
"""
        else:
            string_choose = """    step chooseleaf firstn 0 type host
    step emit
}
"""
        for storage_group_id in storage_groups:
            storage_group = db.storage_group_get(context,storage_group_id)
            storage_group_name = storage_group["name"]
            rule_id = storage_group["rule_id"]
            string = ""
            string = string + "\nrule " + storage_group_name + " {\n"
            string = string + "    ruleset " + str(rule_id) + "\n"
            string = string + sting_common
            string = string + "    step take " + storage_group_name + "\n"
            string = string + string_choose
            self._write_to_crushmap(string)

            #if storage_group_name.find("value_") == -1:
            #    string = ""
            #    string = string + "\nrule " + storage_group_name + " {\n"
            #    string = string + "    ruleset " + str(rule_id) + "\n"
            #    string = string + sting_common
            #    string = string + "    step take " + storage_group_name + "\n"
            #    string = string + string_choose
            #    self._write_to_crushmap(string)
            #else:
            #    string = ""
            #    string = string + "\nrule " + storage_group_name + " {\n"
            #    string = string + "    ruleset " + str(rule_id) + "\n"
            #    string = string + "    type replicated\n    min_size 0\n"
            #    string = string + "    max_size 10\n"
            #    string = string + "    step take " + storage_group_name + "\n"

            #    if zone_tag:
            #        string = string + "    step chooseleaf firstn 1 type zone\n"
            #    else:
            #        string = string + "    step chooseleaf firstn 1 type host\n"
            #    string = string + "    step emit\n"
            #    string = string + "    step take " + \
            #            storage_group_name.replace('value_', '') + "\n"

            #    if zone_tag:
            #        string = string + "    step chooseleaf firstn -1 type zone\n"
            #    else:
            #        string = string + "    step chooseleaf firstn -1 type host\n"
            #    string = string + "    step emit\n}\n" 
            #    self._write_to_crushmap(string)
        return True


    def _gen_rule(self):
        string = """\n# rules
rule capacity {
    ruleset 0
    type replicated
    min_size 0
    max_size 10
    step take capacity
    step chooseleaf firstn 0 type host
    step emit
}

rule performance {
    ruleset 1
    type replicated
    min_size 0
    max_size 10
    step take performance
    step chooseleaf firstn 0 type host
    step emit
}

rule high_performance {
    ruleset 2
    type replicated
    min_size 0
    max_size 10
    step take high_performance
    step chooseleaf firstn 0 type host
    step emit
}

rule value_capacity {
    ruleset 3
    type replicated
    min_size 0
    max_size 10
    step take value_capacity
    step chooseleaf firstn 1 type host
    step emit
    step take capacity
    step chooseleaf firstn -1 type host
    step emit
}

rule value_performance {
    ruleset 4
    type replicated
    min_size 0
    max_size 10
    step take value_performance
    step chooseleaf firstn 1 type host
    step emit
    step take performance
    step chooseleaf firstn -1 type host
    step emit
}

# end crush map
"""
        self._write_to_crushmap(string)


class DiamondDriver(object):
    """Create diamond file"""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        self._diamond_config_path = "/etc/diamond/collectors/"
    def change_collector_conf(self,collector,values):
        '''
        :param collector:
        :param values: {'enabled':True,
                        'interval':15
        }
        :return:
        '''
        # try:
        #     out, err = utils.execute('kill_diamond',
        #                              'll',
        #                              run_as_root=True)
        # except:
        #     LOG.info("kill_diamond error:%s--%s"%(out,err))
        config_file = '%s%s.conf'%(self._diamond_config_path,collector)
        keys = values.keys()
        content = []
        for key in keys:
            content.append('%s=%s'%(key,values[key]))

        out, err = utils.execute('rm','-rf', config_file, run_as_root=True)
        out, err = utils.execute('cp','/etc/vsm/vsm.conf', config_file, run_as_root=True)
        for line in content:
            out, err = utils.execute('sed','-i','1i\%s'%line, config_file, run_as_root=True)
        out, err = utils.execute('sed','-i','%s,$d'%(len(content)+1), config_file, run_as_root=True)
        out, err = utils.execute('service', 'diamond', 'restart', run_as_root=True)
        return out

class ManagerCrushMapDriver(object):
    """Create crushmap file"""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        self.conductor_api = conductor.API()
        self.conductor_rpcapi = conductor_rpcapi.ConductorAPI()
        self._crushmap_path = "/var/run/vsm/mg_crushmap"


    def _write_to_crushmap(self, string):
        utils.execute('chown', '-R', 'vsm:vsm', self._crushmap_path+'_decompiled',
            run_as_root=True)
        fd = open(self._crushmap_path+'_decompiled', 'a')
        fd.write(string)
        fd.close()

    def get_crushmap(self):
        LOG.info("DEBUG Begin to get crushmap")
        utils.execute('ceph', 'osd', 'getcrushmap', '-o',
                self._crushmap_path,'--keyring',FLAGS.keyring_admin, run_as_root=True)
        utils.execute('crushtool', '-d', self._crushmap_path, '-o',
                        self._crushmap_path+'_decompiled', run_as_root=True)
        return True

    def set_crushmap(self):
        LOG.info("DEBUG Begin to set crushmap")
        utils.execute('crushtool', '-c', self._crushmap_path+'_decompiled', '-o',
                        self._crushmap_path, run_as_root=True)
        utils.execute('ceph', 'osd', 'setcrushmap', '-i',
                        self._crushmap_path, run_as_root=True)
        return True


    def _generate_one_rule(self,rule_info):
        '''
        rule_info:{'rule_name':'test-rule',
        'rule_id':None,
        'type':'replicated',
        'min_size':0,
        'max_size':10,
        'takes':[{'take_id':-12,
                'choose_leaf_type':'host',
                'choose_num':2,
                },
                ]

        }
        :return:{'rule_id':3}
        '''

        crushmap = get_crushmap_json_format()
        rule_id = rule_info.get('rule_id',None)
        if rule_id is None:
            rule_ids =[rule['rule_id'] for rule in crushmap._rules]
            rule_ids.sort()
            rule_id = rule_ids[-1]+1
        types = crushmap._types
        types.sort(key=operator.itemgetter('type_id'))
        choose_leaf_type_default = types[1]['name']
        rule_type = rule_info.get('type','replicated')
        min_size = rule_info.get('min_size',0)
        max_size = rule_info.get('max_size',10)
        rule_name = rule_info.get('rule_name')
        takes = rule_info.get('takes')
        sting_common = """    type %s
    min_size %s
    max_size %s
"""%(rule_type,str(min_size),str(max_size))
        string = ""
        string = string + "\nrule " + rule_name + " {\n"
        string = string + "    ruleset " + str(rule_id) + "\n"
        string = string + sting_common
        for take in takes:
            take_name = crushmap.get_bucket_by_id(int(take.get('take_id')))['name']
            take_choose_leaf_type = take.get('choose_leaf_type',choose_leaf_type_default)
            take_choose_num = take.get('choose_num',1)
            string_choose = """    step chooseleaf firstn %s type %s
    step emit
"""%(str(take_choose_num),take_choose_leaf_type)
            string = string + "    step take " + take_name + "\n" + string_choose
        string = string +"    }\n"
        LOG.info('---string-----%s---'%string)
        self.get_crushmap()
        self._write_to_crushmap(string)
        self.set_crushmap()
        return {'rule_id':rule_id}

    def _modify_takes_of_rule(self,rule_info):
        '''
        rule_info:{'rule_name':'test-rule',
        'rule_id':None,
        'type':'replicated',
        'min_size':0,
        'max_size':10,
        'takes':[{'take_id':-12,
                'choose_leaf_type':'host',
                'choose_num':2,
                },
                ]

        }
        :return:{'rule_id':3}
        '''

        crushmap = get_crushmap_json_format()
        rule_name = rule_info.get('rule_name')
        if crushmap.get_rules_by_name(name = rule_name ) is  None:
            return self._generate_one_rule(rule_info)

        types = crushmap._types
        types.sort(key=operator.itemgetter('type_id'))
        choose_leaf_type_default = types[1]['name']
        # rule_type = rule_info.get('type','')
        # min_size = rule_info.get('min_size')
        # max_size = rule_info.get('max_size')

        takes = rule_info.get('takes')

        self.get_crushmap()
        fd = open(self._crushmap_path+'_decompiled', 'r')
        rule_start_line = None
        rule_end_line = None
        insert_take_line = None
        line_number = -1
        lines = fd.readlines()
        fd.close()
        new_lines = []
        LOG.info('rulename=====%s'%rule_name)
        for line in lines:
            line_number += 1
            LOG.info('old lines=====%s----type=%s'%(line,type(line)))
            if 'rule %s {'%rule_name in line:
                rule_start_line = line_number
            if rule_start_line is not None:
                if rule_end_line is None and '}' in line:
                    rule_end_line = line_number
            if rule_start_line is not None and rule_end_line is None:
                if 'ruleset ' in line:
                    rule_id = line[0:-1].split(' ')[-1]
                if 'step take' in line and insert_take_line is None:
                    insert_take_line = line_number
                    #LOG.info('pass--11-%s'%line)
                    continue
                if 'step take' in line and insert_take_line is not None:
                    #LOG.info('pass--22-%s'%line)
                    continue
                if 'step chooseleaf' in line and insert_take_line is not None:
                    #LOG.info('pass--22-%s'%line)
                    continue
                if 'step emit' in line and insert_take_line is not None:
                    #LOG.info('pass--22-%s'%line)
                    continue
            new_lines.append(line)
        if insert_take_line is not None:
            for take in takes:
                take_name = crushmap.get_bucket_by_id(int(take.get('take_id')))['name']
                take_choose_leaf_type = take.get('choose_leaf_type',choose_leaf_type_default)
                take_choose_num = take.get('choose_num',1)
                string = "    step take " + take_name + "\n"
                new_lines.insert(insert_take_line,string)
                string_choose = """    step chooseleaf firstn %s type %s\n"""%(str(take_choose_num),take_choose_leaf_type)
                new_lines.insert(insert_take_line+1,string_choose)
                new_lines.insert(insert_take_line+2,"    step emit\n")
                insert_take_line +=3
        utils.execute('chown', '-R', 'vsm:vsm', self._crushmap_path+'_decompiled',
            run_as_root=True)
        fd = open(self._crushmap_path+'_decompiled', 'w')
        LOG.info('new lines=====%s'%new_lines)
        fd.writelines(new_lines)
        fd.close()
        self.set_crushmap()
        return {'rule_id':rule_id}

    def add_bucket_to_crushmap(self,bucket_name,bucket_type,parent_bucket_type,parent_bucket_name):
        utils.execute("ceph", "osd", "crush", "add-bucket", bucket_name, bucket_type,'--keyring',FLAGS.keyring_admin,
                run_as_root=True)
        utils.execute("ceph", "osd", "crush", "move", bucket_name,
              "%s=%s" % (parent_bucket_type,parent_bucket_name),'--keyring',FLAGS.keyring_admin,
              run_as_root=True)

#     def _generate_one_rule(self,rule_name,take_id_list,rule_id=None,choose_leaf_type=None,choose_num=None,type='replicated',min_size=0,max_size=10):
#         crushmap = get_crushmap_json_format()
#         if rule_id is None:
#             rule_ids =[rule['rule_id'] for rule in crushmap._rules]
#             rule_ids.sort()
#             rule_id = rule_ids[-1]+1
#         if choose_leaf_type is None:
#             types = crushmap._types
#             types.sort(key=operator.itemgetter('type_id'))
#             choose_leaf_type = types[1]['name']
#         sting_common = """    type %s
#     min_size %s
#     max_size %s
# """%(type,str(min_size),str(max_size))
#         string_choose = """    step chooseleaf firstn 1 type %s
#     step emit
# """%choose_leaf_type
#         string = ""
#         string = string + "\nrule " + rule_name + " {\n"
#         string = string + "    ruleset " + str(rule_id) + "\n"
#         string = string + sting_common
#         for take in take_id_list:
#             take_name = crushmap.get_bucket_by_id(int(take))['name']
#             string = string + "    step take " + take_name + "\n" + string_choose
#         string = string +"    }\n"
#         self.get_crushmap()
#         self._write_to_crushmap(string)
#         self.set_crushmap()
#         return {'rule_id':rule_id}
#
#     def _modify_takes_of_rule(self,rule_name,take_id_list,choose_leaf_type=None,choose_num_list=None):
#         crushmap = get_crushmap_json_format()
#         if choose_leaf_type is None:
#             types = crushmap._types
#             types.sort(key=operator.itemgetter('type_id'))
#             choose_leaf_type = types[1]['name']
#         string_choose = """    step chooseleaf firstn 1 type %s
#     step emit
# }
# """%choose_leaf_type
#         self.get_crushmap()
#         fd = open(self._crushmap_path, 'r')
#         rule_start_line = None
#         rule_end_line = None
#         insert_take_line = None
#         line_number = -1
#         lines = fd.readlines()
#         fd.close()
#         new_lines = []
#         # LOG.info('rulename=====%s'%rule_name)
#         # LOG.info('take_id_list=====%s'%take_id_list)
#         # LOG.info('old lines=====%s'%lines)
#         for line in lines:
#             line_number += 1
#             if 'rule %s {'%rule_name in line:
#                 rule_start_line = line_number
#             if rule_start_line is not None:
#                 if rule_end_line is None and '}' in line:
#                     rule_end_line = line_number
#             if rule_start_line is not None and rule_end_line is None:
#                 if 'ruleset ' in line:
#                     rule_id = line[0:-1].split(' ')[-1]
#                 if 'step take' in line and insert_take_line is None:
#                     insert_take_line = line_number
#                     #LOG.info('pass--11-%s'%line)
#                     continue
#                 if 'step take' in line and insert_take_line is not None:
#                     #LOG.info('pass--22-%s'%line)
#                     continue
#                 if 'step chooseleaf' in line and insert_take_line is not None:
#                     #LOG.info('pass--22-%s'%line)
#                     continue
#                 if 'step emit' in line and insert_take_line is not None:
#                     #LOG.info('pass--22-%s'%line)
#                     continue
#             new_lines.append(line)
#         if insert_take_line is not None:
#             for take in take_id_list:
#                 take_name = crushmap.get_bucket_by_id(int(take))['name']
#                 string = "    step take " + take_name + "\n"
#                 new_lines.insert(insert_take_line,string)
#                 string_choose = """    step chooseleaf firstn 1 type %s\n"""%choose_leaf_type
#                 new_lines.insert(insert_take_line+1,string_choose)
#                 new_lines.insert(insert_take_line+2,"    step emit\n")
#                 insert_take_line +=3
#         fd = open(self._crushmap_path, 'w')
#         LOG.info('new lines=====%s'%new_lines)
#         fd.writelines(new_lines)
#         fd.close()
#         self.set_crushmap()
#         return {'rule_id':rule_id}
#
#



def get_crushmap_json_format(keyring=None):
    '''
    :return:
    '''
    if keyring:
        json_crushmap,err = utils.execute('ceph', 'osd', 'crush', 'dump','--keyring',keyring, run_as_root=True)
    else:
        json_crushmap,err = utils.execute('ceph', 'osd', 'crush', 'dump', run_as_root=True)
    crushmap = CrushMap(json_context=json_crushmap)
    return crushmap
