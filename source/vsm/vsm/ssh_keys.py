# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010 OpenStack, LLC.
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

"""
Keys Service
"""

from vsm import flags
from vsm.openstack.common import log as logging

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class SSHManager(object):
    """Chooses a host to create storages."""

    def __init__(self, fpath=FLAGS.authorized_keys):
        self._fpath = fpath or FLAGS.authorized_keys
        self._key_list = open(self._fpath, 'r').readlines()

    def _get_hostname(self, key):
        if key.find('@') != -1:
            return key.split('@')[1].strip()

    def _flush_key_file(self):
        fd = open(self._fpath, 'w')
        for k in self._key_list:
            fd.write(k + '\n')
        fd.close()

    def _find_key(self, key):
        for k in self._key_list:
            if k.find(key.strip()) != -1:
                return True

        return False

    def _append_key(self, key):
        if self._find_key(key) == False:
            self._key_list.append(key)
            fd = open(self._fpath, 'a+')
            fd.write(key)
            fd.close()

    def _is_new_key(self, key):
        host = self._get_hostname(key)
        for k in self._key_list:
            h = self._get_hostname(k)
            if h.find(host) != -1 or host.find(h) != -1:
                return False
        return True

    def _find_old_key(self, key):
        host = self._get_hostname(key)
        for k in self._key_list:
            h = self._get_hostname(k)
            if h.find(host) != -1 or host.find(h) != -1:
                return k
        return None

    def _update_key(self, key):
        if self._find_key(key) == False:
            if self._is_new_key(key):
                self._key_list.remove(self._find_old_key(key))
                self._flush_key_file()
            else:
                self._append_key(key)
