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

    def __init__(self, json_file=None):
        if json_file:
            with open(json_file, 'r') as fh:
                ceph_report = json.load(fh)
            pass
        else:
            ceph_report = self._get_report()

        self._osds = {}
        self._mons = {}
        if ceph_report:
            self._osds = ceph_report['osd_metadata']
            self._mons = ceph_report['monmap']['mons']


    def _get_report(self):
        report = ""
        stderr = ""

        try:
            (report, stderr) = utils.execute('ceph', 'report', run_as_root=True)

            return report
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
        for osd in discover.get_osds():
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
        for mon in discover.get_mons():
            mon_settings += '[mon.%s]\n' %mon['rank']
            mon_settings += 'host = %s\n' %mon['name']
            mon_settings += 'mon addr = %s\n\n' %mon['addr']

        return mon_settings


if __name__ == '__main__':
    discover = cephconf_discover("./report.json")
    print 'osds=%s' %discover.get_osds()
    print 'osd.0=%s' %discover.get_osd(1)

    osd_settings = discover.fixup_osd_settings()
    print osd_settings
    mon_settings = discover.fixup_mon_settings()
    print mon_settings
