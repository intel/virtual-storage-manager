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
Manifest file parser.
"""

import os
from vsm.manifest import sys_info
from vsm import exception
from vsm import flags
from vsm import db
from vsm import context
from vsm.openstack.common import log as logging

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class ManifestParser(object):
    """To parse manifest file

    It's notable that we can parser cluster.manifest
    and server.manifest file. By default we analysis
    server.manifest file. Use as below:

        To analysis server.manifest:
        mpser = ManifestParser()
        mpser = ManifestParser('/etc/manifest/server.manifest', True)

        To analysis cluster.manifest:
        mpser = ManifestParser('/etc/manifest/cluster.manifest', False)

    By using this parser, you hould decide which [].manifest file will be used.
    """

    def __init__(self,
                 fpath=FLAGS.server_manifest,
                 is_server_manifest=True):
        """Set the file path, and which file to parser."""

        # Define two lists below. _disk_type_list need two columns.
        # _single_type_list need just one column.

        #self._disk_type_list = ['ssd', '7200_rpm_sata', '10krpm_sas',
        #       'ssd_cached_7200rpm_sata', 'ssd_cached_10krpm_sas']

        self._context = context.get_admin_context()
        #self._disk_type_list = self._get_disk_type_list()
        self._single_type_list = ['vsm_controller_ip', 'role']

        # Sections in cluster.manifest
        self._cluster_names = ['storage_class',
                               'storage_group', 'cluster',
                               'file_system',
                               'management_addr', 'ceph_public_addr',
                               'ceph_cluster_addr',
                               'storage_group_near_full_threshold',
                               'storage_group_full_threshold',
                               'ceph_near_full_threshold',
                               #'osd_heartbeat_interval',
                               #'osd_heartbeat_grace',
                               'ceph_full_threshold'
                                ]

        self._is_server_manifest = is_server_manifest
        self._file_path = fpath
        if not fpath:
            self._file_path = FLAGS.server_manifest

        if is_server_manifest == False:
            self._file_path = fpath or FLAGS.cluster_manifest

        if not os.path.exists(self._file_path):
            sys_info.wait_disk_ready(self._file_path)
        self._lines = None
        self._read_lines()
        self._check_key_words_exists()
        self._name_dicts = {}
        self._map = {}

    @classmethod
    def parse_cluster_manifest(cls,
                           fpath=FLAGS.cluster_manifest,
                           is_server_manifest=False):
        """Class method to support cluster manifest.

        Support one parser to parse multiple files:
              1. parser = ManifestParser(filepath, False)
                 json_txt = parser.json()
                 json_txt = parser.parse_file(another_file, False)

        """
        inst = cls(fpath, is_server_manifest)
        return inst.format_to_json()

    @classmethod
    def parse_server_manifest(cls,
                   fpath=FLAGS.server_manifest,
                   is_server_manifest=True):
        """Class method to support different usage.

        Support one parser to parse multiple files:
            1. parser = ManifestParser(filepath, True)
               json_txt = parser.json()
               json_txt = parser.parse_file(another_file, True)
        """
        inst = cls(fpath, is_server_manifest)
        return inst.format_to_json()

    def _get_disk_type_list(self):
        group_list = db.storage_group_get_all(self._context)
        disk_type_list = []
        if group_list:
            for item in group_list:
               disk_type_list.append(item['storage_class']) 
        return disk_type_list

    def _read_lines(self):
        """Read self._file_path and return the lines needed.

        Need to do filter operations:
            1. lines full with spaces
            2. comments
            3. comments starts with spaces.
        """
        #print 'self._file_path==',self._file_path
        lines = open(self._file_path).readlines()
        self._lines = []
        for single_line in lines:
            #print 'line^^^^^^^^^^^^^^',single_line
            single_line = single_line.strip()
            if not single_line.startswith("#") and len(single_line):
                self._lines.append(single_line)

    def _check_single_key_word_exists(self, name):
        """Check name exists in this file."""
        # Find the right position of the key word.
        right_pos = -1
        for pos, val in enumerate(self._lines):
            if val.find(name) != -1:
                right_pos = pos
                break

        # If not find, do not raise error to support server_list.
        if right_pos == -1:
            LOG.info("[warning] can not find %s" % name)
            return len(self._lines)

        return right_pos

    def _check_key_words_exists(self):
        """Check all the key words are exists."""

        if not self._lines or len(self._lines) == 0:
            LOG.error('Have not read any lines from file')
            raise exception.NotFound('self._lines in parser are None.')

        #key_words = self._single_type_list + self._disk_type_list
        key_words = self._single_type_list
        for kword in key_words:
            self._check_single_key_word_exists(kword)

    # TODO : need to support multiple controller ip
    def _vsm_controller_ip(self):
        """Get the vsm's controller IP

        It's notable that this IP not just refer to vsm-api node.
        It can refer to two kinds of nodes which can reach to:

            1. Proxy Node with Load Banlance.
            2. VSM-API node. We will have multiple api node running
               in the futhure.
        """
        ip_list = self._get_segment('vsm_controller_ip')
        ip_list = ip_list['single']

        # If there are multiple controller's ip, raise error.
        # We just ignore if these IPs are refer to the same node.
        # We just support one IP here.
        if len(ip_list) > 1:
            LOG.error('Just support one controller IP for VSM.')
            raise exception.DuplicateControllerIPs()

        if len(ip_list) == 0:
            LOG.error('No controller IP for VSM.')
            raise exception.NotFound()

        return ip_list[0]

    #TODO: Delete it later
    #def _number_of_disks(self):
    #    """Return the number of disks."""
    #    counter = 0
    #    for name in self._disk_type_list:
    #        name_dict = self._get_segment(name)
    #        counter = counter + len(name_dict['first'])

    #    return counter

    def _get_segment_from_record_dict(self, name):
        """Get the segment from self._name_dicts if exists."""
        if self._name_dicts.get(name, None):
            return self._name_dicts[name]
        return None

    def _get_cluster_dict(self):
        """Return dict info of cluster."""
        def _get_cluster_value(ktype):
            rpos = self._check_single_key_word_exists(ktype)
            #print 'self.lines=%s-----and pos=%s----'%(self._lines,rpos)
            for pos in (rpos + 1, len(self._lines) - 1):
                single_line = self._lines[pos]
                if single_line.find("[") != -1:
                    break

                seg_list = single_line.split()
                if len(seg_list) == 1:
                    return seg_list[0]

        try:
            mkfs_option = _get_cluster_value('mkfs_option')
        except:
            mkfs_option = None

        try:
            mount_option = _get_cluster_value('mount_option')
        except:
            mount_option = None

        ret = {'cluster_name': _get_cluster_value('cluster'),
               'file_system': _get_cluster_value('file_system'),
               'mkfs_option': mkfs_option,
               'mount_option': mount_option,
               'public_addr': _get_cluster_value('management_addr'),
               'secondary_public_addr':
                              _get_cluster_value('ceph_public_addr'),
               'cluster_addr': _get_cluster_value('ceph_cluster_addr'),
               'osd_heartbeat_interval': _get_cluster_value('osd_heartbeat_interval'),
               'osd_heartbeat_grace': _get_cluster_value('osd_heartbeat_grace')}

        return ret

    def _get_segment(self, name):
        """Get segment of manifest.

        Define manifest as below:
            [ssd]
            /dev/1 /dev/2
            /dev/3 /dev/4

        Put this kind into dict as :
            {'name': 'ssd',
             'first': ['/dev/1', '/dev/3'],
             'second': ['/dev/2', '/dev/4']}

        Also have one style:
            [role]
            storage
            monitor
            mds

        Put this kind into dict as:
            {'name': 'role',
             'single': ['storage', 'monitor', 'mds']}

        Then we change this dict into json as you wanted.
        """
        if name == "cluster":
            return self._get_cluster_dict()

        ret = self._get_segment_from_record_dict(name)
        if ret:
            return ret
        # Make sure this key word exists.
        right_pos = self._check_single_key_word_exists(name)
        ret = {'name': name, 'single': [], 'first': [],
               'second': [], 'third': [], 'fourth': [],
               'fifth': []}

        # Read key word's value into dict.
        # Raise error if find un-matching columns.
        enter_single_column = False
        enter_two_columns = False
        enter_three_columns = False
        enter_four_columns = False
        find_error = False
        for pos in range(right_pos + 1, len(self._lines)):
            single_line = self._lines[pos]
            find_error = enter_single_column and enter_two_columns
            find_error = find_error and enter_three_columns
            find_error = find_error and enter_four_columns

            if not single_line.startswith("[") and find_error == False:
                columns = single_line.split()
                if len(columns) == 5:
                    enter_four_columns = True 
                    ret['first'].append(columns[0])
                    ret['second'].append(columns[1])
                    ret['third'].append(columns[2])
                    ret['fourth'].append(columns[3])
                    ret['fifth'].append(columns[4])
                if len(columns) == 3:
                    enter_three_columns = True
                    ret['first'].append(columns[0])
                    ret['second'].append(columns[1])
                    ret['third'].append(columns[2])
                if len(columns) == 2:
                    enter_two_columns = True
                    ret['first'].append(columns[0])
                    ret['second'].append(columns[1])
                if len(columns) == 1:
                    enter_single_column = True
                    # Write this to support:
                    # storage,monitor,mds
                    parts = columns[0].split(',')
                    ret['single'] = ret['single'] +\
                         [segs for segs in parts if len(segs) > 0]
            else:
                break

        if find_error:
            LOG.error('Columns not match for %s' % name)
            raise
        self._name_dicts['name'] = ret
        return ret

    def _dict_insert_controller_ip(self):
        """Insert vsm controller ip into json format dict."""
        self._map['vsm_controller_ip'] = self._vsm_controller_ip()
        self._map['cluster_ip'] = self._vsm_controller_ip()

    def _dict_insert_role(self):
        """Insert role into json format dict."""
        name_dict = self._get_segment('role')
        self._map['role'] = ""

        if len(name_dict['single']) == 0:
            LOG.error('Find 0 role, format error')
            name_dict['single'] = ['unspecified']
            #raise

        for node_role in name_dict['single']:
            self._map['role'] = node_role + ',' + self._map['role']

    def _dict_insert_zone(self):
        """Insert zone into json format dict."""
        name_dict = self._get_segment('zone')
        self._map['zone'] = ""

        if len(name_dict['single']) > 1:
            LOG.error('Format error: more than 2 zone were given.')
            raise

        if len(name_dict['single']) == 0:
            LOG.debug('Use default zone: %s' % FLAGS.default_zone)
            name_dict['single'].append(FLAGS.default_zone)

        for single_zone in name_dict['single']:
            self._map['zone'] = single_zone

    def _dict_insert_auth_key(self):
        """Insert auth key into json format dict."""
        name_dict = self._get_segment('auth_key')
        self._map['auth_key'] = ""

        if len(name_dict['single']) > 1 or \
           len(name_dict['single']) == 0:
            LOG.error('Find 0 or multiple auth_key, format error')
            raise

        for auth_key in name_dict['single']:
            self._map['auth_key'] = auth_key

    def _dict_insert_storage_class(self, storage_type):
        """Try to insert storage class into json format dict."""
        name_dict = self._get_segment(storage_type)
        if len(name_dict['first']) != len(name_dict['second']):
            LOG.error('The first row must be the same as second row')
            raise

        if self._map.get("storage_class", None) is None:
            self._map["storage_class"] = []

        storage_class = {'name': storage_type, 'disk': []}
        for idx in range(0, len(name_dict['first'])):
            one_disk = {"osd": name_dict['first'][idx],
                        "journal": name_dict['second'][idx]}
            storage_class['disk'].append(one_disk)

        self._map["storage_class"].append(storage_class)

    def _dict_insert_sys_info(self):
        """Insert into system info."""
        if not self._map:
            self._map = {}

        self._map["host"] = sys_info.get_hostname()
        self._map["ip"] = sys_info.get_local_ip()
        self._map["id_rsa_pub"] = sys_info.get_rsa_key()

    def _format_server_manifest_to_json(self, check_manifest_tag):
        """Transfer the server manifest file into json format dict."""
        self._map = {}
        if not check_manifest_tag:
            disk_type_list = self._get_disk_type_list()
            for disk_type in disk_type_list:
                self._dict_insert_storage_class(disk_type)

        self._dict_insert_controller_ip()
        self._dict_insert_role()
        self._dict_insert_zone()
        self._dict_insert_auth_key()
        #self._map['drive_num'] = self._number_of_disks()
        self._dict_insert_sys_info()

        # Refer to the same ip
        self._map['cluster_ip'] = self._map['vsm_controller_ip']
        self._map['controller_ip'] = self._map['vsm_controller_ip']
        #self._map['device_type_list'] = disk_type_list
        return self._map

    def _dict_insert_ntp_keys(self):
        self._map["ntp_keys"] = sys_info.get_ntp_keys()

    def _dict_insert_storage_class_c(self):
        """Insert storage_class into json format dict."""
        name_dict = self._get_segment('storage_class')

        if len(name_dict['single']) == 0:
            LOG.error('Format error, at least 1 storage class should be given')
            raise

        self._map['storage_class'] = []
        for storage_class in name_dict['single']:
            self._map['storage_class'].append(storage_class)

    def _dict_insert_periodic_parameters_c(self):
        name_dict = self._get_segment('storage_group_near_full_threshold')
        if len(name_dict['single']) == 0:
            LOG.error('Format error, at least, need set' + \
                      'storage_group_near_full_threshold')
        self._map['storage_group_near_full_threshold'] = name_dict['single']

        name_dict = self._get_segment('storage_group_full_threshold')
        if len(name_dict['single']) == 0:
            LOG.error('Format error, at least, need set' + \
                      'storage_group_full_threshold')
        self._map['storage_group_full_threshold'] = name_dict['single']

    def _dict_insert_zone_c(self):
        """Insert zone into json format dict."""
        name_dict = self._get_segment('zone')
        self._map['zone'] = []

        zone_list = list(name_dict['single'])
        if len(zone_list) != len(name_dict['single']):
            LOG.error("There is exist duplicate zone, please check")

        for zone in zone_list:
            self._map['zone'].append(zone)

        if len(self._map['zone']) == 0:
            self._map['zone'].append(FLAGS.default_zone)

    def _dict_insert_openstack_ip_c(self):
        """ Insert Openstack nova compute and cinder volume nodes'
            ip into json format
        """
        name_dict = self._get_segment('openstack_ip')
        self._map['openstack_ip'] = list()

        nova_set = set(name_dict['single'])
        if len(nova_set) != len(name_dict['single']):
            LOG.error("There is exist duplicate ip, please check")

        for ip in nova_set:
            self._map['openstack_ip'].append(ip)

    def _dict_insert_storage_group_c(self):
        """Insert storage_group into json format dict."""
        name_dict = self._get_segment('storage_group')

        if len(name_dict['first']) == 0:
            LOG.error('Format error, at least 1 storage group should be given')
            raise

        self._map['storage_group'] = []
        for idx in range(0, len(name_dict['first'])):
            one_storage_group = {"name": name_dict['first'][idx],
                                 "friendly_name": name_dict['second'][idx],
                                 "storage_class": name_dict['third'][idx]}
            self._map['storage_group'].append(one_storage_group)

    def _dict_insert_cluster_c(self):
        """Return the segments of cluster name."""
        #return self._get_segment("cluster")
        self._map['cluster'] = self._get_segment("cluster")

    def _dict_insert_ceph_conf(self):
        """ Return the segments of ceph_conf."""
        name_dict = self._get_segment("ceph_conf")
        LOG.info('name_dict===%s'%name_dict)
        self._map['ceph_conf'] = []
        for idx in range(0, len(name_dict['first'])):
            ceph_conf = {'name': name_dict['first'][idx],
                       'default_value': name_dict['second'][idx]}
            self._map['ceph_conf'].append(ceph_conf)
        LOG.info("ceph_conf (key/value) set: %s" % self._map['ceph_conf'])

    def _dict_insert_settings_c(self):
        """ Return the segments of vsm settings."""
        name_dict = self._get_segment("settings")
        #LOG.info("settings (key/value) set: %s" % self._map['settings'])
        self._map['settings'] = []
        for idx in range(0, len(name_dict['first'])):
            setting = {'name': name_dict['first'][idx],
                       'default_value': name_dict['second'][idx]}
            self._map['settings'].append(setting)

    def _dict_insert_cache_tier_defaults_c(self):
        """ Return the segments of cache_tier default value."""
        name_dict = self._get_segment("cache_tier_defaults")
        self._map['cache_tier_defaults'] = []
        for idx in range(0, len(name_dict['first'])):
            setting = {'name': name_dict['first'][idx],
                       'default_value': name_dict['second'][idx]}
            self._map['cache_tier_defaults'].append(setting)

    def _dict_insert_server_list_c(self):
        """Insert server_list into json format dict"""
        name_dict = self._get_segment('server_list')
        if len(name_dict['single']) == 0:
            return

        self._map['server_list'] = []
        for server in name_dict['single']:
            self._map['server_list'].append(server)

    def _dict_insert_ec_profiles_c(self):
        """Return the segments of erasure code profiles"""
        name_dict = self._get_segment("ec_profiles")
        print name_dict
        LOG.info("ec_profiles:%s" % name_dict) 
        print name_dict

        if len(name_dict['first']) == 0:
            # NOTE: we may have to support old version of cluster.manifest file.
            return
            LOG.error('Format error, at least 1 storage group should be given')
            raise

        self._map['ec_profiles'] = []
        for idx in range(0, len(name_dict['first'])):
            one_ec_profile = {"name": name_dict['first'][idx],
                                 "plugin_path": name_dict['second'][idx],
                                 "plugin": name_dict['third'][idx],
                                 "pg_num": name_dict['fourth'][idx],
                                 "plugin_kv_pair": name_dict['fifth'][idx]} 
            self._map['ec_profiles'].append(one_ec_profile)

    def _trans_between_db(self):
        """Write this info for writing into DB."""
        if not self._map:
            return
        info = self._map['cluster']
        self._map['cluster']['name'] = info["cluster_name"]
        self._map['cluster']['management_network'] = info["public_addr"]
        self._map['cluster']['ceph_public_network'] = \
            info["secondary_public_addr"]
        self._map['cluster']['cluster_network'] = info["cluster_addr"]
        self._map['cluster']['file_system'] = info["file_system"]
    def _format_cluster_manifest_to_json(self):
        """Return the json format [dict]."""
        self._map = {}
        self._dict_insert_storage_class_c()
        self._dict_insert_zone_c()
        self._dict_insert_storage_group_c()
        self._dict_insert_cluster_c()
        self._dict_insert_server_list_c()
        self._dict_insert_ntp_keys()
        self._dict_insert_openstack_ip_c()
        self._dict_insert_settings_c()
        self._dict_insert_cache_tier_defaults_c()
        self._dict_insert_ec_profiles_c()
        self._dict_insert_ceph_conf()
        #self._dict_insert_periodic_parameters_c()
        self._trans_between_db()
        return self._map

    def format_to_json(self, check_manifest_tag=False):
        """Transfer the manifest file into json format dict"""
        if self._is_server_manifest:
            return self._format_server_manifest_to_json(check_manifest_tag)
        else:
            return self._format_cluster_manifest_to_json()

