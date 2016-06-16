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
Tools for accessing and managing ceph configuration content.
"""

import os
import uuid
import hashlib
import ConfigParser
from cStringIO import StringIO
from vsm import utils
from vsm import exception
from vsm import context as vsm_context
from vsm import manager
from vsm import flags
from vsm import db
from vsm.agent import rpcapi as agent_rpc
from vsm.openstack.common import log as logging


LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS


class ClusterIdAccessor:
    """
    Read and cache the cluster id from /opt/stack/data/vsm/cluster_id the first
    time get_cluster_id() is called; thereafter, retrieve the cached value.
    """

    _cluster_id = None

    def __init__(self):
        pass

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


class ConfigInfo:
    """
    Base class for specific types of config info. Provides the fields and the getters for these fields.
    """
    _content = ""
    _md5sum = ""
    _luts = 0

    def __init__(self):
        pass

    def get_content(self):
        return self._content

    def get_md5sum(self):
        return self._md5sum

    def get_luts(self):
        return self._luts


class DBConfigInfo(ConfigInfo):
    """
    A subclass of ConfigInfo that works specifically for accessing data and metadata of the database copy of
    ceph configuration data.
    """

    def __init__(self, accessor, context):
        """
        Read the db cluster:ceph_conf, cluster:ceph_conf_md5, and cluster:ceph_conf_luts. If the cluster_id
        cannot be obtained, or if these db fields are not yet populated, just return an empty string for the
        contents and the md5 and zero for the timestamp, but don't throw an exception. Since content is stripped
        before being written to the db, there's no need to strip content on the way out here.
        :param accessor: the cluster id accessor to use to access the correct row in the cluster table.
        :param context: the database access context - for rights.
        """
        ConfigInfo.__init__(self)
        cluster_id = accessor.get_cluster_id()
        if cluster_id:
            self._content = db.cluster_get_ceph_conf(context, cluster_id)
            dbmeta = db.cluster_get_ceph_conf_metadata(context, cluster_id)
            if 'ceph_conf_md5sum' in dbmeta:
                self._md5sum = dbmeta['ceph_conf_md5sum']
            if 'ceph_conf_luts' in dbmeta:
                self._luts = dbmeta['ceph_conf_luts']


class FileConfigInfo(ConfigInfo):
    """
    A subclass of ConfigInfo that works specifically for accessing data and metadata of a file system copy of
    ceph configuration data.
    """

    def __init__(self, fp, sync):
        """
        Read the file into a memory buffer. If sync is True, also read the file's meta data. If the file
        doesn't exist just return an empty string for the file contents, but don't throw an exception.
        :param fp: the file path to read from. File content is stripped as it's read in so that md5 check sums
        for empty files will match that of empty content from the database.
        :param sync: if true, read the file last write timestamp and generate an md5 checksum on the data.
        """
        ConfigInfo.__init__(self)
        try:
            self._content = utils.read_file_as_root(fp).strip()
            if sync:
                statbuf = os.stat(fp)
                self._luts = int(statbuf.st_mtime)
                self._md5sum = hashlib.md5(self._content).hexdigest()
        except (exception.FileNotFound, os.error):
            pass


class CephConfigSynchronizer:
    """
    Provides functionality to synchronize the latest updates from either the VSM database or a cluster node's ceph
    configuration file (/etc/ceph/ceph.conf). The algorithm used for synchronizing master ceph configuration files
    is as follows:

    When CephConfigSynchronizer().sync_before_read() is called (with 'sync' == True [default]) the system compares
    md5 check sums of the DB copy and the local file system copy. If they're different, the system checks the last
    update timestamp (luts) of each of these copies to see which one is newer. If the DB copy is newer, it's written
    to the file system. If the file system copy is newer, it's written to the DB and the other agents are notified.
    """

    _cluster_id_accessor = ClusterIdAccessor()
    _context = vsm_context.get_admin_context()
    _host = FLAGS.host

    def __init__(self):
        pass

    def _write_ceph_conf_to_db(self, content):
        """
        Write specified content to db. 'content' is stripped before write so empty content will match an empty file's
        md5 check sum.
        :param content: the ceph configuration file content to be written to the database
        """
        cluster_id = self._cluster_id_accessor.get_cluster_id()
        if not cluster_id:
            LOG.debug('Can not get cluster_id; unable to save ceph.conf to db')
            return

        db.cluster_update_ceph_conf(self._context, cluster_id, content.strip())

    def _request_all_remote_agents_update_ceph_conf_from_db(self):
        """
        Send a message to all remote agents to perform a sync between their /etc/ceph/ceph.conf and the db ceph conf.
        """
        server_list = db.init_node_get_all(self._context)
        for ser in server_list:
            if ser['host'] != self._host:
                LOG.debug("notifying %s to sync with db" % ser['host'])
                agent_rpc.AgentAPI().update_ceph_conf(self._context, ser['host'])

    def sync_before_read(self, cfgfile, sync=True):
        """
        Check DB cluster:ceph_conf against fp if sync is True. If checksums are different or (only) one of them does
        not exist, compare timestamps. Timestamp of missing entity is always considered older than the existing entity.
        If DB is newer, write DB to file. If file is newer, sync DB from file and signal agents to sync with DB. Parse
        file if it exists.

        :param cfgfile: the file path from which to parse config data (ok for file to not exist).
        :param sync: sync if True, otherwise just parse specified file if exists.
        :return: The latest config content - from db or file (if sync==False, always from file)
        """
        fpinfo = FileConfigInfo(cfgfile, sync)
        latest_content = fpinfo.get_content()
        LOG.debug("fpinfo: %.30s, %s, %d" % (fpinfo.get_content(), fpinfo.get_md5sum(), fpinfo.get_luts()))
        if sync:
            dbinfo = DBConfigInfo(self._cluster_id_accessor, self._context)
            LOG.debug("dbinfo: %.30s, %s, %d" % (dbinfo.get_content(), dbinfo.get_md5sum(), dbinfo.get_luts()))
            if fpinfo.get_md5sum() != dbinfo.get_md5sum():
                LOG.debug("md5sums different, checking last update timestamp")
                if fpinfo.get_luts() > dbinfo.get_luts():
                    LOG.debug("file timestamp greater than db timestamp; writing file to db and notifying agents")
                    self._write_ceph_conf_to_db(latest_content)
                    self._request_all_remote_agents_update_ceph_conf_from_db()
                else:
                    LOG.debug("db timestamp greater than file timestamp; writing db to file")
                    latest_content = dbinfo.get_content() + '\n'
                    utils.write_file_as_root(cfgfile, latest_content, "w")

        return latest_content

    def sync_after_write(self, content):
        """
        Write 'content' to DB then notify all agents to sync now.
        :param content: the ceph configuration data to be sent to the DB and pulled by all nodes.
        """
        LOG.debug("updating db: %.30s" % content)
        self._write_ceph_conf_to_db(content)
        self._request_all_remote_agents_update_ceph_conf_from_db()


class CephConfigParser(manager.Manager):
    """
    Wrap and extend an instance of python config parser to manage configuration data parsed from a ceph
    configuration file (normally found in /etc/ceph/$cluster.conf - where $cluster is often 'ceph').
    """

    def _load_ceph_conf_from_dict(self, dict_cfg):
        """
        Load ceph configuration parameters from a section:options dictionary of dictionaries.
        :param dict_cfg: {section: {option:value, option:value}, section...}
        :return: None
        """
        try:
            for section, options in dict_cfg.iteritems():
                self._parser.add_section(section)
                for option, value in options.iteritems():
                    self._parser.set(section, option, value)
        except:
            raise TypeError("dict_cfg must be a dict of dicts - {section:{option:value,...},...}")

    def __init__(self, fp=None, sync=True, *args, **kwargs):
        """
        Build a python ConfigParser capable of properly parsing a ceph configuration file. Primarily, this means
        replacing the optionxform function with one that treats option names with underscores the same as those
        without, and in a case-insensitive manner.

        If the file path (fp) is not empty and it's either a string or unicode string then attempt to read the
        contents of that file into the parser (though the CephConfigSynchronizer's sync_before_read method to give
        this file a chance to be synchronized into the database if it's newer than the db version).

        If the file path is a dictionary, attempt to parse it as a dictionary representation of configuration file
        content, e.g., {section:{option:value,...},...}.

        :param fp: an optional file path or configuration dictionary
        :param sync: sync with db before reading the file path above if true
        :param args: not used
        :param kwargs: not used
        """
        super(CephConfigParser, self).__init__(*args, **kwargs)
        self._parser = ConfigParser.ConfigParser()
        self._parser.optionxform = lambda optname: optname.lower().replace(' ', '_')

        if fp is not None:
            if isinstance(fp, str) or isinstance(fp, unicode):
                self._parser.readfp(StringIO(CephConfigSynchronizer().sync_before_read(fp, sync)))
            elif isinstance(fp, dict):
                self._load_ceph_conf_from_dict(fp)
            else:
                raise TypeError("'fp' must be a string or dictionary")

    def sections(self):
        """
        Return a list of section names in the parser's configuration file contents.
        :return: a list of section names in python list format.
        """
        return self._parser.sections()

    def get(self, section, option, default=None):
        """
        Return the value of a specified option in a specified section, the specified default value if the specified
        section and/or option are not found in the configuration content.
        :param section: the section in which to look.
        :param option: the option for which to look.
        :param default: the default value to use in case section and/or option are missing.
        :return: the desired section/option value, or the default is missing.
        """
        return self._parser.get(section, option, default)

    def set(self, section, key, value):
        """
        Set the value of the specified option in the specified section.
        :param section: the section in which to write.
        :param key: the option to set.
        :param value: the value to which the specified section/option should be set.
        """
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        self._parser.set(section, key, value)

    def as_dict(self):
        """
        Return the entire configuration content as a dictionary in the form: {section:{option:value,...},...}
        :return: the entire configuration content as a dictionary of dictionaries.
        """
        sections = {}
        for section in self._parser.sections():
            sections[section] = dict(self._parser.items(section))
        return sections

    def as_str(self):
        """
        Return the entire configuration content as a single string, including line breaks.
        :return: the parser content as a string.
        """
        sfp = StringIO()
        self._parser.write(sfp)
        return sfp.getvalue()

    def save_conf(self, file_path=FLAGS.ceph_conf, sync=True):
        """
        Save the current contents of the parser as a configuration file named as per the file_path argument. If
        sync is True, also write contents into the database and notify remote users to sync with updated content.

        :param file_path: the file to which the parser contents should be saved.
        :param sync: assuming we just updated (because we're saving), write the contents to the db and notify remote
        agents if True, otherwise do not write to db and notify agents.
        """
        content = self.as_str()
        utils.write_file_as_root(file_path, content, "w")
        if sync:
            CephConfigSynchronizer().sync_after_write(content)

    def add_global(self, dict_kvs=None):
        """
        Add a ceph [global] section to the configuration content.
        :param dict_kvs: a dictionary of values to be added to the [global] section.
        """
        if dict_kvs is None:
            dict_kvs = {}
        dict_kvs['max_file'] = dict_kvs.get('max_file', 131072)
        dict_kvs['is_cephx'] = dict_kvs.get('is_cephx', True)
        dict_kvs['down_out_interval'] = dict_kvs.get('down_out_interval', 90)
        dict_kvs['pool_default_size'] = dict_kvs.get('pool_default_size', 3)

        section = 'global'
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        if not dict_kvs['is_cephx']:
            self._parser.set(section, 'auth supported', 'none')
        else:
            self._parser.set(section, 'auth supported', 'cephx')
        self._parser.set(section, 'max open files', dict_kvs['max_file'])
        self._parser.set(section, 'mon osd down out interval', dict_kvs['down_out_interval'])

        for key, value in dict_kvs.items():
            if key not in ['max_file', 'is_cephx', 'down_out_interval', 'pool_default_size']:
                self._parser.set(section, key, value)

        # Must add fsid for create cluster in newer version of ceph.
        # In order to support lower version of vsm.
        # We set keyring path here.
        # keyring = /etc/ceph/keyring.admin
        self._parser.set(section, 'keyring', '/etc/ceph/keyring.admin')
        # Have to setup fsid.
        self._parser.set(section, 'fsid', uuid.uuid1())

    def add_mds_header(self, dict_kvs=None):
        """
        Add a ceph [mds] section to the configuration content.
        :param dict_kvs: a dictionary of values to be added to the [mds] section.
        """
        if dict_kvs is None:
            dict_kvs = {}
        if self._parser.has_section('mds'):
            return
        dict_kvs['keyring'] = dict_kvs.get('keyring', 'false')

        section = 'mds'
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        self._parser.set(section, 'mds data', '/var/lib/ceph/mds/ceph-$id')
        self._parser.set(section, 'mds standby replay', dict_kvs['keyring'])
        self._parser.set(section, 'keyring', '/etc/ceph/keyring.$name')
        for key, value in dict_kvs.items():
            if key not in ['keyring']:
                self._parser.set(section, key, value)

    def add_mon_header(self, dict_kvs=None):
        """
        Add a ceph [mon] section to the configuration content.
        :param dict_kvs: a dictionary of values to be added to the [mon] section.
        """
        if dict_kvs is None:
            dict_kvs = {}
        if self._parser.has_section('mon'):
            return
        dict_kvs['clock_drift'] = dict_kvs.get('clock_drift', 200)
        dict_kvs['cnfth'] = dict_kvs.get('cnfth', None)
        dict_kvs['cfth'] = dict_kvs.get('cfth', None)

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
        for key, value in dict_kvs.items():
            if key not in ['clock_drift', 'cnfth', 'cfth']:
                self._parser.set(section, key, value)

    def add_osd_header(self, dict_kvs=None):
        """
        Add a ceph [osd] section to the configuration content.
        :param dict_kvs: a dictionary of values to be added to the [osd] section.
        """
        if dict_kvs is None:
            dict_kvs = {}
        if self._parser.has_section('osd'):
            return
        dict_kvs['journal_size'] = dict_kvs.get('journal_size', 0)
        dict_kvs['osd_type'] = dict_kvs.get('osd_type', 'xfs')
        dict_kvs['osd_heartbeat_interval'] = dict_kvs.get('osd_heartbeat_interval', 10)
        dict_kvs['osd_heartbeat_grace'] = dict_kvs.get('osd_heartbeat_grace', 10)
        dict_kvs['mount_options'] = dict_kvs.get('mount_options')

        section = 'osd'
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        # NOTE Do not add osd data here.
        self._parser.set(section, 'osd journal size', dict_kvs['journal_size'])
        self._parser.set(section, 'filestore xattr use omap', 'true')
        self._parser.set(section, 'osd crush update on start', 'false')
        osd_data = "/var/lib/ceph/osd/osd$id"
        self._parser.set(section, 'osd data', osd_data)
        # NOTE add keyring to support lower version of OSD.
        # keyring = /etc/ceph/keyring.$name
        self._parser.set(section, 'keyring', '/etc/ceph/keyring.$name')
        self._parser.set(section, 'osd heartbeat interval', dict_kvs['osd_heartbeat_interval'])
        self._parser.set(section, 'osd heartbeat grace', dict_kvs['osd_heartbeat_grace'])
        self._parser.set(section, 'osd mkfs type', dict_kvs['osd_type'])

        # Below is very important for set file system.
        # Do not change any of them.
        format_type = '-f'
        if dict_kvs['osd_type'].lower() == 'ext4':
            format_type = '-F'
        self._parser.set(section, 'osd mkfs options %s' % dict_kvs['osd_type'], format_type)
        for key, value in dict_kvs.items():
            if key not in ['journal_size', 'osd_type', 'osd_heartbeat_interval', 'osd_heartbeat_grace']:
                self._parser.set(section, key, value)

    def add_rgw(self, rgw_sec, host, keyring, log_file, rgw_frontends,
                rgw_region=None, rgw_zone=None, rgw_zone_root_pool=None):
        """
        Add a ceph [client.<name>] section to the configuration content.
        :param rgw_sec: should be passed as '[client.<name>]'
        :param host: the host where the client is running.
        :param keyring: the client keyring to be set.
        :param log_file: client log file to be set.
        :param rgw_frontends: the client front end list to be set.
        :param rgw_region: the client region to be set.
        :param rgw_zone: the client zone to be set.
        :param rgw_zone_root_pool: the client zone root pool to be set.
        """
        if self._parser.has_section(rgw_sec):
            self._parser.remove_section(rgw_sec)
        self._parser.add_section(rgw_sec)
        if rgw_region:
            self._parser.set(rgw_sec, "rgw region", rgw_region)
        if rgw_zone:
            self._parser.set(rgw_sec, "rgw zone", rgw_zone)
        if rgw_zone_root_pool:
            self._parser.set(rgw_sec, "rgw zone root pool", rgw_zone_root_pool)
        self._parser.set(rgw_sec, "host", host)
        self._parser.set(rgw_sec, "keyring", keyring)
        self._parser.set(rgw_sec, "log file", log_file)
        self._parser.set(rgw_sec, "rgw frontends", rgw_frontends)

    # ----------------------------------------------------------------------------------------------------
    # NOTE: The following methods are deprecated since ceph.conf files no longer require [TYP.X] sections
    #       Some work should be done to remove the need for these methods in calling code.

    def __get_type_number(self, sec_type):
        cnt = 0
        for sec in self._parser.sections():
            if sec.lower().find(sec_type.lower()) != -1:
                cnt += 1
        return cnt

    def get_mon_num(self):
        return self.__get_type_number('mon.')

    def get_mds_num(self):
        return self.__get_type_number('mds.')

    def get_osd_num(self):
        return self.__get_type_number('osd.')

    def add_mon(self, hostname, ip, mon_id):
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
        sec = 'mds.%s' % mds_id
        if self._parser.has_section(sec):
            return

        if not self._parser.has_section(sec):
            self._parser.add_section(sec)
        self._parser.set(sec, 'host', hostname)
        self._parser.set(sec, 'public addr', '%s' % ip)

    def add_osd(self, hostname, pub_addr, cluster_addr, osd_dev, journal_dev, osd_id):
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
        sec = '%s.%s' % (typ, num)
        if not self._parser.has_section(sec):
            return True
        return self._parser.remove_section(sec)

    def remove_mds_header(self):
        if not self._parser.has_section('mds'):
            return True
        return self._parser.remove_section('mds')

    def remove_osd(self, osd_id):
        return self._remove_section('osd', osd_id)

    def remove_mon(self, mon_id):
        return self._remove_section('mon', mon_id)

    def remove_mds(self, mds_id):
        return self._remove_section('mds', mds_id)

    # NOTE: End of deprecated code section (see previous note).
    # ----------------------------------------------------------------------------------------------------
