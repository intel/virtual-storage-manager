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
Agent Service
"""

import os
import json
import re
import time
from vsm import exception
from vsm import flags
from vsm.openstack.common import log as logging
from vsm import utils

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

def set_keyring_admin(keyring_admin):
    """Set keyring admin file."""
    if not os.path.exists(FLAGS.keyring_admin):
        #open(FLAGS.keyring_admin, 'w').write(keyring_admin)
        utils.write_file_as_root(FLAGS.keyring_admin, keyring_admin, "w")
    else:
        LOG.info('Error keyring file exists')
        LOG.info('Back up & cover the old version')
        old_content = open(FLAGS.keyring_admin, 'r').read()
        # if not the same. cmp('a', 'a') == 0
        if cmp(keyring_admin.strip(), old_content.strip()):
            bfx = time.asctime().replace(' ','_').replace(':','_')
            old_fname = FLAGS.keyring_admin + bfx
            #open(old_fname, 'w').write(old_content)
            utils.write_file_as_root(old_fname, old_content, "w")
            # write the newer version.
            #open(FLAGS.keyring_admin, 'w').write(keyring_admin)
            utils.write_file_as_root(FLAGS.keyring_admin, keyring_admin, "w")
        else:
            LOG.info('Have the same content, pass')

def is_vsm_ok():
    """Check vsm.conf is configured."""
    vcf = file(FLAGS.vsm_config).read()
    apf = file(FLAGS.api_paste_config).read()

    if re.search("MYSQL_VSM_PASSWORD", vcf)\
       or re.search("MYSQL_VSM_USER", vcf)\
       or re.search("RABBITMQ_HOST", vcf)\
       or re.search("RABBITMQ_PASSWORD", vcf)\
       or re.search("RABBITMQ_PORT", vcf)\
       or re.search("SERVICE_TENANT_NAME", apf)\
       or re.search("SERVICE_USER", apf)\
       or re.search("SERVICE_PASSWORD", apf):
        #utils.execute("rm", "-rf", "/root/.ssh/", run_as_root=True)
        #os.popen('rm -rf /root/.ssh/')
        return False
    return True

def set_vsm_conf(recv):
    """Write vsm conf files."""
    if recv is None:
        return False

    old_recv = recv
    try:
        recv = json.loads(recv)
    except TypeError:
        recv = old_recv
        LOG.info('Maybe recv is not json.')

    if not recv.get("api-paste.ini", None):
        LOG.error('Can not find content of api-paste.ini')
        raise exception.NotFound()

    if not recv.get("vsm.conf", None):
        LOG.error('Can not find content of vsm.conf')
        raise exception.NotFound()

    files = ["api-paste.ini", "vsm.conf"]
    for conf in files:
        conf_path = FLAGS.vsm_config_path + conf
        #conf_file = open(conf_path, 'w')
        #conf_file.write(recv[conf])
        utils.write_file_as_root(conf_path, recv[conf], "w")
        #conf_file.close()

    return True
