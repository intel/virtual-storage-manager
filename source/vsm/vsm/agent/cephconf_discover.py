# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright 2012 Red Hat, Inc.
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

"""Crush map parser..

Parse crush map in json format, and identify storage groups from ruleset.

"""
import json
import operator
from vsm import utils
from vsm import exception
from vsm.openstack.common import log as logging
from vsm import flags

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class cephconf_discover():

    def __init__(self, json_file=None, keyring=None):
        self._keyring = keyring
        if json_file:
            with open(json_file, 'r') as fh:
                ceph_report = json.load(fh)
            pass
        else:
            ceph_report = self._get_report()

        self._osds = {}
        self._mons = {}
        self.ceph_report = ceph_report
        if ceph_report:
            self._osds = ceph_report['osd_metadata']
            self._mons = ceph_report['monmap']['mons']


    def _get_report(self):
        report = ""
        stderr = ""
        try:
            if self._keyring:
                (report, stderr) = utils.execute('ceph', 'report','--keyring',self._keyring, run_as_root=True)
            else:
                (report, stderr) = utils.execute('ceph', 'report', run_as_root=True)
            return json.loads(report)
        except exception.ProcessExecutionError:
            LOG.warn('Fail to get report from ceph: %s' % stderr)


    def get_osds(self):
        return self._osds

    def get_osd(self, id=0):
        # osd_fields = ['devs','host','cluster addr','public addr','osd journal']
        if (id >= 0):
            if id < len(self._osds):
                return self._osds[id]

    def fixup_osd_settings(self):
        # enumerate osds
        osd_settings = "\n"
        for osd in self.get_osds():
            osd_settings += '[osd.%s]\n' %osd['id']
            osd_settings += 'host = %s\n' %osd['hostname']
            osd_settings += 'devs = %s\n' %osd['osd_data']
            osd_settings += 'osd journal = %s\n' %osd['osd_journal']
            osd_settings += 'cluster addr = %s\n' %osd['back_addr']
            osd_settings += 'public addr = %s\n\n' %osd['front_addr']

        return osd_settings

    def get_mons(self):
        return self._mons

    def get_mon(self, id=0):
        if (id >= 0):
            if id < len(self._mons):
                return self._mons[id]

    def fixup_mon_settings(self):
        # enumerate mons
        # mon_fields = ['host','mon addr']
        mon_settings = "\n"
        for mon in self.get_mons():
            mon_settings += '[mon.%s]\n' %mon['rank']
            mon_settings += 'host = %s\n' %mon['name']
            mon_settings += 'mon addr = %s\n\n' %mon['addr']

        return mon_settings

    def detect_ceph_conf(self):
        global_value_dict = {'heartbeat_interval':10,
        'osd_pool_default_size':self.ceph_report["osdmap"]['pools'][0]['size'],
        'osd_heartbeat_grace':10,
        'fsid':self.ceph_report["osdmap"]["fsid"],
        }
        global_settings = '''
[global]
heartbeat interval = %(heartbeat_interval)s
osd pool default size = %(osd_pool_default_size)s
osd heartbeat grace = %(osd_heartbeat_grace)s
keyring = /etc/ceph/keyring.admin
fsid = %(fsid)s
auth supported = cephx
        '''%(global_value_dict)
        osd_header_settings ='''
[osd]
osd mount options xfs = rw,noatime,inode64,logbsize=256k,delaylog
osd crush update on start = false
filestore xattr use omap = true
keyring = /etc/ceph/keyring.$name
osd mkfs type = %(mkfs_type)s
osd data = /var/lib/ceph/osd/osd$id
osd heartbeat interval = 10
osd heartbeat grace = 10
osd mkfs options xfs = -f
osd journal size = 0
        '''%({'mkfs_type':self.ceph_report["osd_metadata"][0].get('filestore_backend','xfs')})
        mon_header_settings ='''
[mon]
mon osd full ratio = .90
mon data = /var/lib/ceph/mon/mon$id
mon osd nearfull ratio = .75
mon clock drift allowed = .200
        '''
        osd_settings = self.fixup_osd_settings()
        mon_settings = self.fixup_mon_settings()
        cephconf = global_settings + '\n' \
                    + osd_header_settings + '\n' \
                    + osd_settings + '\n' \
                    + mon_header_settings + '\n' \
                    + mon_settings + '\n'
        return cephconf

if __name__ == '__main__':
    discover = cephconf_discover("./report.json")
    print 'osds=%s' %discover.get_osds()
    print 'osd.0=%s' %discover.get_osd(1)

    osd_settings = discover.fixup_osd_settings()
    print osd_settings
    mon_settings = discover.fixup_mon_settings()
    print mon_settings
