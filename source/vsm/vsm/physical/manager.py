
# Copyright 2014 Intel Corporation, All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the"License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Physical Service
"""
import os
import json
from vsm import db
from vsm import flags
from vsm import context
from vsm import manager
from vsm.conductor import rpcapi as conductor_rpcapi
from vsm.openstack.common import log as logging
from vsm.openstack.common.periodic_task import periodic_task
from vsm.physical import driver

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class PhysicalManager(manager.Manager):
    """PhysicalManager is mainly used to manage physical nodes."""

    RPC_API_VERSION = '1.2'

    def __init__(self, service_name=None, *args, **kwargs):
        super(PhysicalManager, self).__init__(*args, **kwargs)
        self.driver = driver.load_physical_driver()
        self._conductor_rpcapi = conductor_rpcapi.ConductorAPI()
        self._log_printed = False

    @periodic_task
    def update_disk_device(self, context):
        hostname = FLAGS.host
        device_list = self._conductor_rpcapi.\
                      device_get_by_hostname(context, hostname)
        if device_list:
            for device in device_list:
                values = {}
                if not os.path.exists(device['path']):
                    device_state = FLAGS.partition_status_missing
                else:
                    device_state = FLAGS.partition_status_ok
                values['state'] = device_state
                    #usage = self.driver.get_disk_usage(device['name'])
                    #device['total_capacity_kb'] = usage.total / 1024
                    #device['avail_capacity_kb'] = usage.free / 1024
                    #device['used_capacity_kb'] = usage.used / 1024
                if not os.path.exists(device['journal']):
                    journal_state = FLAGS.partition_status_missing
                else:
                    journal_state = FLAGS.partition_status_ok
                values['journal_state'] = journal_state

                db.device_update(context, device['id'], values)
