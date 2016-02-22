# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Inc.
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

import json
from vsm import utils
from vsm.api.openstack import wsgi
from vsm.api import xmlutil
from vsm import flags
from vsm import db
from vsm.openstack.common import log as logging
from vsm.api.views import agents as agents_views
from vsm import context
from vsm.agent import appnodes
from vsm.manifest.parser import ManifestParser
from vsm.openstack.common.db import exception as db_exc

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

def make_agent(elem, detailed=False):
    elem.set('id')
    elem.set('host')
    elem.set('service_id')
    elem.set('primary_public_ip')
    elem.set('secondary_public_ip')
    elem.set('cluster_ip')
    elem.set('raw_ip')
    elem.set('zone_id')
    elem.set('type')
    elem.set('cluster_id')
    elem.set('data_drives_number')
    elem.set('status')
    elem.set('id_rsa_pub')

    if detailed:
        pass

    #xmlutil.make_links(elem, 'links')

def _translate_agent_summary_view(agent):
    """Get detail of agent information."""
    d = {"id": agent.get("id", ""),
        "host": agent.get("host", ""),
        "primary_public_ip": agent.get("primary_public_ip", ""),
        "secondary_public_ip": agent.get("secondary_public_ip", ""),
        "cluster_ip": agent.get("cluster_ip", ""),
        "raw_ip": agent.get("raw_ip", ""),
        "service_id": agent.get("service_id", ""),
        "zone_id": agent.get("zone_id", ""),
        "cluster_id": agent.get("cluster_id", ""),
        "data_drives_number": agent.get('data_drives_number', ""),
        "type": agent.get('type', ""),
        "id_rsa_pub": agent.get('id_rsa_pub', ""),
        "status": agent.get('status', "")}
    return d

agent_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class AgentTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('agent', selector='agent')
        make_agent(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=agent_nsmap)

class AgentsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('agents')
        elem = xmlutil.SubTemplateElement(root, 'agent', selector='agents')
        make_agent(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=agent_nsmap)

class AgentsController(wsgi.Controller):
    """The Agents API controller for the OpenStack API.

    -----------------
    NOTE: Do not use rpcapi class in Controller class.
    Try to avoid using RPC in services init function.

    Because after the services is running. RabbitMQ can
    be using for it.

    ==
    So just use db here.
    """
    _view_builder_class = agents_views.ViewBuilder

    def _get_keyring_admin_from_db(self):
        """Get keyring from DB."""

        # If already have keyring.admin just fetch once.
        if self._cluster_info.get('keyring_admin', None):
            LOG.info(' API contains the keyring.admin')
            return

        cluster_info = self._cluster_info['cluster']
        cluster_name = cluster_info['cluster_name']
        cluster_ref = db.cluster_get_by_name(self._context,
                                             cluster_name)

        if not cluster_ref:
            LOG.info(' No keyring_admin cluster = %s' % cluster_name)
            return
        else:
            # NOTE we update the cluster info in DB.
            LOG.info(' Find cluster name = %s' % cluster_name)
            # If we find the cluster, we also return the keyring.admin
            # info for storage nodes.
            info_dict = cluster_ref.get('info_dict', None)
            if info_dict:
                keyring_admin = json.loads(info_dict)
                keyring_admin_info = keyring_admin.get('keyring_admin', None)
                if keyring_admin:
                    self._cluster_info['keyring_admin'] = keyring_admin_info
                    LOG.info(' API get keyring.admin from DB.')
                else:
                    LOG.info('Can not get keyring_admin from DB.')
            else:
                LOG.info('Can not get info_dict from DB.')
            return True

    def _write_cluster_info(self):
        """Write cluster info into DB.

        Info includes:

            cluster_name
            file_system
            public_address
            secondary_public_address
            cluster_address
        """
        cluster_info = self._cluster_info['cluster']

        LOG.info(' cluster_info to db = %s' % \
            json.dumps(cluster_info, sort_keys=True, indent=4))

        cluster_name = cluster_info['cluster_name']

        cluster_ref = db.cluster_get_by_name(self._context,
                                             cluster_name)

        if not cluster_ref:
            LOG.info(' Have not find cluster = %s' % cluster_name)
            LOG.info(' Before Writing cluster = %s' % \
            json.dumps(cluster_info, sort_keys=True, indent=4))
            db.cluster_create(self._context, cluster_info)
        else:
            # NOTE we update the cluster info in DB.
            LOG.info(' Find cluster name = %s' % cluster_name)
            db.cluster_update(self._context,
                              cluster_ref['id'],
                              cluster_info)
            # If we find the cluster, we also return the keyring.admin
            # info for storage nodes.
            info_dict = cluster_ref['info_dict']
            if info_dict:
                LOG.info('Get info dict from DB.')
                keyring_admin = json.loads(info_dict).get('keyring_admin', None)
                self._cluster_info['keyring_admin'] = keyring_admin
            else:
                LOG.info('Can not get keyring from DB.')
            return True

    def _write_zone_info(self):
        """Write zone into DB.

        Zone list:
            zone_a
            zone_b
            zone_c

        Just write names here.
        """
        #TODO add zone table two variables. cluster_id, storage_group_id.
        zone_list = self._cluster_info['zone']
        for zone_name in zone_list:
            zone_ref = db.\
                          zone_get_by_name(self._context, zone_name)
            if not zone_ref:
                LOG.info('Have not find zone = %s' % zone_name)
                db.zone_create(self._context,
                                               {'name': zone_name,
                                                'deleted': False})
            else:
                LOG.info('Find zone = %s in zone Table.' % zone_name)
        return True

    def _write_ec_profiles(self):
        if not self._cluster_info.get('ec_profiles', None):
            return True

        profile_list = self._cluster_info['ec_profiles']
        for profile in profile_list:
            db.ec_profile_update_or_create(self._context, profile) 

        return True

    def _write_cache_tier_defaults(self):
        if not self._cluster_info.get('cache_tier_defaults', None):
            return True
        cache_tier_defaults = self._cluster_info['cache_tier_defaults']
        LOG.info("CLUSTER INFO")
        LOG.info(cache_tier_defaults)
        name_list = []
        sets = db.vsm_settings_get_all(self._context)
        db_list = [s.name for s in sets]
        for setting in cache_tier_defaults:
            LOG.info(setting)
            name = setting.get('name', None)
            value = setting.get('default_value', None)
            if not name in db_list:
                try:
                    if not value.isdigit():
                        value = float(value)
                except ValueError:
                    value = None
                except AttributeError:
                    value = None
                if not value:
                    LOG.warn('The default value of %s should be digit. Load default value ...' % name)
                    value = FLAGS.get(name, None)
                    if not value:
                        LOG.warn('Failed to load the default value of %s.' % name)
                        try:
                            raise exception.GetNoneError
                        except exception.GetNoneError as e:
                            LOG.error("%s:%s" %(e.code, e.message))
                        ret = False
                        continue
                setting['value'] = value
                ref = db.vsm_settings_update_or_create(self._context, setting)
                name_list.append(name)




    def _write_vsm_settings(self):
        """Writing vsm settings into DB.

           [settings]
           #format [key] [default_value]
           storage_group_near_full_threshold 65
           storage_group_full_threshold 85

        """
        ret = True
        setting_list = self._cluster_info['settings']
        name_list = list()
        sets = db.vsm_settings_get_all(self._context)
        db_list = [s.name for s in sets]
        LOG.debug('vsm settings already exists in db: %s' % db_list)

        for setting in setting_list:
            try:
                name = setting.get('name', None)
                value = setting.get('default_value', None)
                # The setting does not exist in db.
                if not name in db_list:
                    if not value or not value.isdigit():
                        LOG.warn('The default value of %s should be digit. Load default value ...' % name)
                        value = FLAGS.get(name, None)
                        if not value:
                            LOG.warn('Failed to load the default value of %s.' % name)
                            try:
                                raise exception.GetNoneError
                            except exception.GetNoneError as e:
                                LOG.error("%s:%s" %(e.code, e.message))
                            ret = False
                            continue
                    setting['value'] = value
                    ref = db.vsm_settings_update_or_create(self._context,
                                                           setting)
                    name_list.append(name)
            except:
                ret = False
                LOG.error('Failed to load setting %s.' % name)
                continue

        # load other default vsm settings from flags
        setting_list = name_list + db_list
        LOG.debug('settings loaded: %s' % setting_list)
        for ss in flags.vsm_settings_opts:

            if not ss.name in setting_list:
                try:
                    val = {
                        'name': ss.name,
                        'value': str(ss.default),
                        'default_value': str(ss.default)
                    }
                    ref = db.vsm_settings_update_or_create(self._context,
                                                           val)
                except:
                    ret = False
                    LOG.error('Failed to load setting %s from flags.' % name)
                continue

        return ret

    def _write_openstack_ip(self):
        """ Write Openstack nova controller ips
            and cinder volume ips into DB.

         Openstack Ips:
            10.239.82.xx
            10.239.82.yy
         Just write Ip addr here.
        """
        ip_list = self._cluster_info['openstack_ip']
        if ip_list:
            try:
                # fake one user id and project id
                self._context.user_id = 32 * '1'
                self._context.project_id = 32 * '1'
                node_list = appnodes.create(self._context, ip_list, allow_duplicate=True)
                #LOG.debug('app nodes added %s' % node_list)
                for node in node_list:
                    status = 'reachable'
                    appnodes.update(self._context, node.id, status)
            except Exception as e:
                LOG.error('Failed to add app nodes with error %s' % e)
                return False
        return True

    def _write_storage_groups(self):
        """Write storage groups into DB.

        At here we have to write info as below:

            name, storage_class, friendly_name, rule_id, deleted,take_order.

        --------------------------------------------------------
        Important
        =========
        rule_id, in ceph system. The must be started from 0.
        Assume there are 0, 1, 2, 3 four storage groups, delete the
        iter=2 storage group, then all numbers will changed to be
        0 1 2. In fact, old {3}'s number is changed to be 2.

        For insert, we must follow one by one.
        """
        #TODO storage group need to contains cluster_id.

        stg_list = self._cluster_info['storage_group']
        for rule_id, stg in enumerate(stg_list):
            stg['rule_id'] = rule_id
            stg['status'] = FLAGS.storage_group_in
            stg['take_order'] = 0
            stg['choose_num'] = 0
            stg['choose_type'] = 'host'
            # TODO change the create_storage_group api.
            # DB create_storage_group will ignore the
            # request if the stg has exists.
            db.create_storage_group(self._context,
                        values=stg)
            LOG.info('Write storage group = %s success.' % stg['name'])
        return True

    def _store_cluster_info_to_db(self):
        """Store the cluster.manifest info into db.

        We have to insert info into db as follow:

            1. cluster name, public addresses etc.
            2. zone list.
            3. storage group list.

        Although there four segs in cluster.manifest.
        [stoarge_class] and [storage_group] refer to
        storage_group.

        """
        # TODO add info into db.tables.
        # Need Zone tables containse cluster.id ad forein key.
        # Insert cluster name and addresses.
        LOG.info(' agents.py _store_cluster_info_to_db()')
        write_cluster_ret = self._write_cluster_info()
        write_zone_ret = self._write_zone_info()
        write_storage_groups = self._write_storage_groups()
        write_openstack_ip = self._write_openstack_ip()
        write_settings = self._write_vsm_settings()
        write_ec_profiles = self._write_ec_profiles()
        write_cache_tier_defaults = self._write_cache_tier_defaults()

        self._have_write_cluter_into_db = \
            write_cluster_ret and write_zone_ret \
            and write_storage_groups and write_openstack_ip \
            and write_settings and write_ec_profiles \
            and write_cache_tier_defaults

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        self._context = context.get_admin_context()
        self.smp = ManifestParser(FLAGS.cluster_manifest, False)
        self._cluster_info = self.smp.format_to_json()
        LOG.info(' Get data from manifest file = %s' %\
            json.dumps(self._cluster_info, sort_keys=True, indent=4))
        vsm_conf = open(FLAGS.vsm_config, 'r').read()
        api_paste = open(FLAGS.api_paste_config, 'r').read()
        self._cluster_info['vsm.conf'] = vsm_conf
        self._cluster_info['api-paste.ini'] = api_paste
        self._have_write_cluter_into_db = False
        LOG.info(' running before writing DB.')
        self._store_cluster_info_to_db()
        super(AgentsController, self).__init__()

    def _get_agent_search_options(self):
        """Return agent search options allowed by non-admin."""
        return ('id', 'name', 'public_ip')

    def _get_storage_group_and_class_list(self):
        list = db.storage_group_get_all(self._context)
        storage_group_list = []
        storage_class_list = []
        if list:
            for item in list:
                value = {}
                value['friendly_name'] = item['friendly_name']
                value['name'] = item['name']
                value['rule_id'] = item['rule_id']
                value['storage_class'] = item['storage_class']
                storage_group_list.append(value)
                if not item['storage_class'] in storage_class_list:
                    storage_class_list.append(item['storage_class'])
        return storage_group_list, storage_class_list

    @wsgi.serializers(xml=AgentsTemplate)
    def index(self, req):
        """Return vsm-controller's info and configures."""
        try:
            self._get_keyring_admin_from_db()
            if self._have_write_cluter_into_db == False:
                self._store_cluster_info_to_db()
        except:
            LOG.error('Write DB error occurs in agents.index()')

        if req.environ['vsm.context']:
            LOG.info('context is not None')
        self._cluster_info['etc_hosts'] = \
             utils.read_file_as_root(FLAGS.etc_hosts)
        storage_group , storage_class = self._get_storage_group_and_class_list()
        self._cluster_info['storage_class'] = storage_class
        self._cluster_info['storage_group'] = storage_group
        return self._cluster_info

def create_resource(ext_mgr):
    return wsgi.Resource(AgentsController(ext_mgr))
