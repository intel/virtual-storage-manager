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
Drivers for Agent Services.
"""

from oslo.config import cfg
from vsm import flags
from vsm import utils
from vsm.physical import driver
from vsm.physical.worker import cpu as cpu_worker
from vsm.physical.worker import network as network_worker
from vsm.physical.worker import disk as disk_worker
from vsm.physical.worker import memory as memory_worker
from vsm.openstack.common.gettextutils import _
from vsm.openstack.common import log as logging

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class GeneralDriver(driver.PhysicalDriver):
    """General class for Physical Driver.

    """

    def __init__(self):
        super(GeneralDriver, self).__init__()
        self._cpu_worker = cpu_worker.CPUWorker()
        self._network_worker = network_worker.NetworkWorker()
        self._disk_worker = disk_worker.DiskWorker()
        self._memory_worker = memory_worker.MemoryWorker()

    #def init_host(self):
    #    """Initialize anything that is necessary for the driver."""
    #    #cpu_cores = self._cpu_worker.get_cpu_cores()
    #    #LOG.info("general:cpu cores:%s" % cpu_cores)
    #    ips = self._network_worker.get_ips()
    #    LOG.info("general:ips:%s" % ips)
    #    disk_partitions = self._disk_worker.get_disk_partitions()
    #    LOG.info("general:disk_partitions:%s" % disk_partitions)
    #    mem_total = self._memory_worker.get_mem_total()
    #    LOG.info("general:mem_total:%s" % mem_total)
    #    hostname = self._host_worker.get_hostname()
    #    LOG.info("general:hostname:%s" % hostname)

    #def get_disk_usage(self, path):
    #    return self._disk_worker.get_disk_usage(path)

