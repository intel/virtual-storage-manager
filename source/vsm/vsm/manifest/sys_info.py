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
Collect system information.
"""

import os
import time
import socket
from vsm import flags
from vsm.openstack.common import log as logging
from vsm import utils

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

def get_hostname():
    """Return the hostname."""
    #TODO change the style of get hostname.
    return socket.gethostname()

def get_local_ip():
    """Return the ip address."""
    #TODO use python code to get ip address.
    ip_list = os.popen("hostname -I").read().strip()
    return ip_list.replace(' ', ',')

def get_rsa_key():
    """Return public key of this server."""
    #TODO change the style to get rsa key.
    key, err = utils.execute("cat", FLAGS.id_rsa_pub, run_as_root=True)
    return key

def get_ntp_keys():
    """Return public key of this server."""
    #TODO change the style to get rsa key.
    if not os.path.exists(FLAGS.ntp_keys):
        return None
    wait_disk_ready(FLAGS.ntp_keys)
    key = open(FLAGS.ntp_keys).read()
    return key

def wait_disk_ready(file_path, run_times=3):
    """Wait disk ready for file store"""
    try_times = 1
    #while not os.path.exists(file_path):
    while not utils.file_is_exist_as_root(file_path):
        time.sleep(1)
        try_times = try_times + 1
        if try_times > run_times:
            LOG.error('Can not find the %s'%file_path)
            raise
