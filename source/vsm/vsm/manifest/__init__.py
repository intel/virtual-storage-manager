#    Copyright 2014 Intel
#    All Rights Reserved
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
Used by Agent Service to connect with Controller.
In order to get key parameters to set configuration files.
"""

import time
from vsm.manifest import config
from vsm.manifest.wsgi_client import WSGIClient
from vsm.manifest.parser import ManifestParser
from vsm.openstack.common import log as logging
from vsm import flags

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class AgentChecker(object):
    """Agent Checker is used to check agent services.

    AgentChecker is used to add into vsm clusters.
    if vsm_is_configed:
        start_as_usuall
    else:
        get_config_from_controller.
        config_vsm_files
    """
    def __init__(self, fpath=FLAGS.server_manifest):
        self._file_path = fpath
        self._smp = ManifestParser(self._file_path)
        self._send_data = self._smp.format_to_json(check_manifest_tag=True)
        self._server_host = self._send_data['vsm_controller_ip']
        self._sender = WSGIClient(self._server_host,
                        self._send_data['auth_key'])

    def config_vsm_files(self):
        """Begin to config vsm configuration files."""
        # If vsm.conf changes, vsm-agent update the configuration files.
        # need to add file comparation operation.
        can_connect = False
        while can_connect == False:
            try:
                recive_data = self._sender.index()
                can_connect = True
            except:
                time.sleep(10)
                LOG.info('Can not connect to vsm-api. reconnect.')

        # If find the keyring_admin update it?
        if recive_data.get('keyring_admin', None):
            LOG.info('Get keyring.admin from DB.')
            config.set_keyring_admin(recive_data['keyring_admin'])
        else:
            LOG.info('Can not get keyring from DB.')

        if not config.is_vsm_ok():
            config.set_vsm_conf(recive_data)
            return True
        else:
            LOG.info('vsm.conf is ok now. skip this configuration.')
            return False
