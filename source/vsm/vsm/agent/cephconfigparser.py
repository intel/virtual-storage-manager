# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

# pylint: disable=W0212
# pylint: disable=R0913
# pylint: disable=W0233
# pylint: disable=W0231

"""
Tools for ceph config.
"""

import os
import uuid
import ConfigParser
from cStringIO import StringIO
from vsm import utils
from vsm import context as vsm_context
from vsm import manager
from vsm import flags
from vsm import db
from vsm.agent import rpcapi as agent_rpc
from vsm.openstack.common import log as logging

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class CephConfigParser(manager.Manager):
    """
    Wrap and extend an instance of python config parser to manage configuration data parsed from a ceph
    configuration file (normally found in /etc/ceph/$cluster.conf - where $cluster is often 'ceph').
    """

    class ClusterIdAccessor():
        """
        Read and cache the cluster id from /opt/stack/data/vsm/cluster_id the first
        time get_cluster_id() is called; thereafter, retrieve the cached value.
        """
        _cluster_id = None

        def get_cluster_id(self):
            """
            Cache and return the cluster id. If the local copy is not yet set, read it from the
            cluster_id file, and then cache and return it, else just return the cached copy.
            :return: the cluster id found in /opt/stack/data/vsm/cluster_id.
            """
            if not self._cluster_id:
                cluster_id_file = os.path.join(FLAGS.state_path, 'cluster_id')
                if os.path.exists(cluster_id_file):
                    self._cluster_id = utils.read_file_as_root(cluster_id_file).strip()
            return self._cluster_id

    _cluster_id_accessor = ClusterIdAccessor()
    _context = vsm_context.get_admin_context()

    def _load_ceph_conf_from_dict(self, dict_cfg):
        """
        Load ceph configuration parameters from a section:options dictionary of dictionaries.
        :param dict_cfg: {section: {option:value, option:value}, section...}
        :return: none
        """
        try:
            for section,options in dict_cfg.iteritems():
                self._parser.add_section(section)
                for option,value in options.iteritems():
                    self._parser.set(section, option, value)
        except:
            raise TypeError("dict_cfg must be a dict of dicts - {section:{option:value,...},...}")

    def __init__(self, fp=None, *args, **kwargs):
        super(CephConfigParser, self).__init__(*args, **kwargs)
        self._parser = ConfigParser.ConfigParser()
        self._parser.optionxform = lambda optname: optname.lower().replace(' ', '_')

        # NOTE: fp can be a file name in str or unicode format OR a dictionary of dictionaries

        if fp is not None:
            if isinstance(fp, str) or isinstance(fp, unicode):
                self._parser.read(fp)
            elif isinstance(fp, dict):
                self._load_ceph_conf_from_dict(fp)
            else:
                raise TypeError("'fp' must be a string or dictionary")

    # NOTE: The following methods are obsolete since ceph.conf files no longer contain [mon.X], [mds.X], and [ods.X] sections

    def __get_type_number(self, sec_type):
        cnt = 0
        for sec in self._parser._sections:
            if sec.lower().find(sec_type.lower()) != -1:
                cnt = cnt + 1
        return cnt

    def get_mon_num(self):
        return self.__get_type_number('mon.')

    def get_mds_num(self):
        return self.__get_type_number('mds.')

    def get_osd_num(self):
        return self.__get_type_number('osd.')

    # NOTE: End of obsolete code section (see previous note).

    def as_dict(self):

        # NOTE: There is no equivalent to this routine in python's ConfigParser; calling code should be reworked
        # to call another routine that's more efficient relative to ConfigParser, and a new method should be added
        # to this code that provides access to these other ConfigParser routines.

        sections = {}
        for section in self._parser.sections():
            sections[section] = dict(self._parser.items(section))
        return sections

    def add_global(self, dict_kvs={}):

        # NOTE: Possibly found in dict_kvs:
        #     is_cephx=True
        #     max_file=131072
        #     down_out_interval=90
        #     pool_default_size=3

        dict_kvs['max_file'] = dict_kvs.get('max_file',131072)
        dict_kvs['is_cephx'] = dict_kvs.get('is_cephx',True)
        dict_kvs['down_out_interval'] = dict_kvs.get('down_out_interval',True)
        dict_kvs['pool_default_size'] = dict_kvs.get('pool_default_size',3)

        section = 'global'
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        if not dict_kvs['is_cephx']:
            self._parser.set(section, 'auth supported', 'none')
        else:
            self._parser.set(section, 'auth supported', 'cephx')
        self._parser.set(section, 'max open files', str(dict_kvs['max_file']))
        self._parser.set(section, 'mon osd down out interval', str(dict_kvs['down_out_interval']))

        for key,value in dict_kvs.items():
            if key not in ['max_file','is_cephx','down_out_interval','pool_default_size']:
                self._parser.set(section, key, str(value))

        # Must add fsid for create cluster in newer version of ceph.
        # In order to support lower version of vsm.
        # We set keyring path here.
        # keyring = /etc/ceph/keyring.admin
        self._parser.set(section, 'keyring', '/etc/ceph/keyring.admin')
        # Have to setup fsid.
        self._parser.set(section, 'fsid', str(uuid.uuid1()))

    def add_mds_header(self, dict_kvs={}):
        if self._parser.has_section('mds'):
            return
        dict_kvs['keyring'] = dict_kvs.get('keyring','false')

        section = 'mds'
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        self._parser.set(section, 'mds data', '/var/lib/ceph/mds/ceph-$id')
        self._parser.set(section, 'mds standby replay', dict_kvs['keyring'])
        self._parser.set(section, 'keyring', '/etc/ceph/keyring.$name')
        for key,value in dict_kvs.items():
            if key not in ['keyring']:
                self._parser.set(section, key, str(value))

    def add_mon_header(self, dict_kvs={}):
        if self._parser.has_section('mon'):
            return
        dict_kvs['clock_drift'] = dict_kvs.get('clock_drift',200)
        dict_kvs['cnfth'] = dict_kvs.get('cnfth',None)
        dict_kvs['cfth'] = dict_kvs.get('cfth',None)

        section = 'mon'
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        # NOTE: The default mon data dir set in ceph-deploy is in: /var/lib/ceph/mon/ceph-$id/
        # In order to support created by mkcephfs and live update,
        # we have to set it to: mon_data="/var/lib/ceph/mon/mon$id"
        mon_data = "/var/lib/ceph/mon/mon$id"
        self._parser.set(section, 'mon data', mon_data)
        self._parser.set(section, 'mon clock drift allowed', '.' + str(dict_kvs['clock_drift']))
        if dict_kvs['cfth']:
            self._parser.set(section, 'mon osd full ratio', '.' + str(dict_kvs['cfth']))
        if dict_kvs['cnfth']:
            self._parser.set(section, 'mon osd nearfull ratio', '.' + str(dict_kvs['cnfth']))
        for key,value in dict_kvs.items():
            if key not in ['clock_drift','cnfth','cfth']:
                self._parser.set(section, key, str(value))

    def _update_ceph_conf_into_db(self, content):
        cluster_id = self._cluster_id_accessor.get_cluster_id()
        if not cluster_id:
            LOG.debug('Can not get cluster_id; unable to save ceph.conf to db')
            return

        db.cluster_update_ceph_conf(self._context, cluster_id, content)

    def _push_db_conf_to_all_agents(self):
        server_list = db.init_node_get_all(self._context)
        for ser in server_list:
            agent_rpc.AgentAPI().update_ceph_conf(self._context, ser['host'])

    def content(self):
        sfp = StringIO()
        self._parser.write(sfp)
        return sfp.getvalue()

    def save_conf(self, file_path=FLAGS.ceph_conf):
        content = self.content()
        utils.write_file_as_root(file_path, content)
        self._update_ceph_conf_into_db(content)
        self._push_db_conf_to_all_agents()

    def add_mon(self, hostname, ip, mon_id):

        # NOTE: This routine is obsolete since ceph.conf no longer requires [mon.X] sections.

        sec = 'mon.%s' % mon_id
        if self._parser.has_section(sec):
            return

        if not self._parser.has_section(sec):
            self._parser.add_section(sec)
        self._parser.set(sec, 'host', hostname)
        ips = ip.split(',')
        ip_strs = ['%s:%s' % (i, str(6789)) for i in ips]
        ip_str = ','.join(ip_strs)
        self._parser.set(sec, 'mon addr', ip_str)

    def add_mds(self, hostname, ip, mds_id):

        # NOTE: This routine is obsolete since ceph.conf no longer requires [mds.X] sections.

        sec = 'mds.%s' % mds_id
        if self._parser.has_section(sec):
            return

        if not self._parser.has_section(sec):
            self._parser.add_section(sec)
        self._parser.set(sec, 'host', hostname)
        self._parser.set(sec, 'public addr', '%s' % ip)

    def add_osd_header(self, dict_kvs={}):
        if self._parser.has_section('osd'):
            return
        dict_kvs['journal_size'] = dict_kvs.get('journal_size',0)
        dict_kvs['osd_type'] = dict_kvs.get('osd_type','xfs')
        dict_kvs['osd_heartbeat_interval'] = dict_kvs.get('osd_heartbeat_interval',10)
        dict_kvs['osd_heartbeat_grace'] = dict_kvs.get('osd_heartbeat_grace',10)

        section = 'osd'
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        # NOTE Do not add osd data here.
        self._parser.set(section, 'osd journal size', str(dict_kvs['journal_size']))
        self._parser.set(section, 'filestore xattr use omap', 'true')
        self._parser.set(section, 'osd crush update on start', 'false' )
        osd_data = "/var/lib/ceph/osd/osd$id"
        self._parser.set(section, 'osd data', osd_data)
        # NOTE add keyring to support lower version of OSD.
        # keyring = /etc/ceph/keyring.$name
        self._parser.set(section, 'keyring', '/etc/ceph/keyring.$name')
        self._parser.set(section, 'osd heartbeat interval', str(dict_kvs['osd_heartbeat_interval']))
        self._parser.set(section, 'osd heartbeat grace', str(dict_kvs['osd_heartbeat_grace']))
        self._parser.set(section, 'osd mkfs type', dict_kvs['osd_type'])
        cluster = db.cluster_get_all(self._context)[0]
        mount_option = cluster['mount_option']
        if not mount_option:
            mount_option = utils.get_fs_options(dict_kvs['osd_type'])[1]
        self._parser.set(section, 'osd mount options %s' % dict_kvs['osd_type'], mount_option)

        # Below is very important for set file system.
        # Do not change any of them.
        format_type = '-f'
        if dict_kvs['osd_type'].lower() == 'ext4':
            format_type = '-F'
        self._parser.set(section, 'osd mkfs options %s' % dict_kvs['osd_type'], format_type)
        for key,value in dict_kvs.items():
            if key not in ['journal_size','osd_type','osd_heartbeat_interval','osd_heartbeat_grace']:
                self._parser.set(section, key, str(value))

    def add_osd(self, hostname, pub_addr, cluster_addr, osd_dev, journal_dev, osd_id):

        # NOTE: This routine is obsolete since ceph.conf no longer requires [osd.X] sections.

        sec = 'osd.%s' % osd_id
        if self._parser.has_section(sec):
            return

        if not self._parser.has_section(sec):
            self._parser.add_section(sec)
        if hostname is None \
           or pub_addr is None\
           or cluster_addr is None \
           or journal_dev is None \
           or osd_dev is None:
            LOG.error('cephconfigparser error, all parameters are empty')
            raise

        self._parser.set(sec, 'host', hostname)

        # a list or tuple of public ip
        if hasattr(pub_addr, '__iter__'):
            ip_str = ','.join([ip for ip in pub_addr])
            self._parser.set(sec, 'public addr', ip_str)
        else:
            self._parser.set(sec, 'public addr', pub_addr)

        self._parser.set(sec, 'cluster addr', cluster_addr)
        self._parser.set(sec, 'osd journal', journal_dev)
        self._parser.set(sec, 'devs', osd_dev)

    def _remove_section(self, typ, num):

        # NOTE: This routine is obsolete since ceph.conf no longer requires [TYP.X] sections.

        sec = '%s.%s' % (typ, num)
        if not self._parser.has_section(sec):
            return True
        return self._parser.remove_section(sec)

    def remove_mds_header(self):
        if not self._parser.has_section('mds'):
            return True
        return self._parser.remove_section('mds')

    def remove_osd(self, osd_id):

        # NOTE: This routine is obsolete since ceph.conf no longer requires [osd.X] sections.

        return self._remove_section('osd', osd_id)

    def remove_mon(self, mon_id):

        # NOTE: This routine is obsolete since ceph.conf no longer requires [mon.X] sections.

        return self._remove_section('mon', mon_id)

    def remove_mds(self, mds_id):

        # NOTE: This routine is obsolete since ceph.conf no longer requires [mds.X] sections.

        return self._remove_section('mds', mds_id)

    def add_rgw(self, rgw_sec, host, keyring, log_file, rgw_frontends):
        if self._parser.has_section(rgw_sec):
            self._parser.remove_section(rgw_sec)
        self._parser.add_section(rgw_sec)
        self._parser.set(rgw_sec, "host", host)
        self._parser.set(rgw_sec, "keyring", keyring)
        self._parser.set(rgw_sec, "log file", log_file)
        self._parser.set(rgw_sec, "rgw frontends", rgw_frontends)
