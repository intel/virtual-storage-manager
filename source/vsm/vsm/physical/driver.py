
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
Drivers for get diff physical devices.
"""

from oslo.config import cfg
from vsm import flags
from vsm import utils
from vsm.openstack.common import importutils
from vsm.openstack.common.gettextutils import _
from vsm.openstack.common import log as logging

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

physical_driver_opts = [
    cfg.StrOpt('physical_driver',
               default='vsm.physical.general.GeneralDriver',
               help='Driver to use for controller storage system.'
                    'include: vsm.physical.general.GeneralDriver'),
]

CONF = cfg.CONF
CONF.register_opts(physical_driver_opts)

def load_physical_driver(physical_driver=None):
    """Load ad physical driver module.

    Load the physical driver module specified by the physical_driver
    configuration option or, if supplied, the driver name supplied
    as an argument.

    :param physical_driver: a physical driver name to override the config opt.
    :returns: a PhysicalDriver interface.
    """
    if not physical_driver:
        physical_driver = CONF.physical_driver

    if not physical_driver:
        LOG.warn(_("Physical driver option required, but not specified"))
        raise

    try:
        # If just write driver.CephDriver
        driver = importutils.import_object_ns('vsm.physical',
                                              physical_driver)
        return utils.check_isinstance(driver, PhysicalDriver)
    except ImportError:
        try:
            # If vsm.physical.driver.CephDriver
            driver = importutils.import_object(physical_driver)
            return utils.check_isinstance(driver, PhysicalDriver)
        except ImportError:
            LOG.exception(_("Unable to load the physical driver"))
            raise

class PhysicalDriver(object):
    """Basic class for Physical Driver.

    The physical Driver mainly use to manage physical nodes in
    the cluster.

    Now we implement the generaldriver which just can do what general
    physical servers do. For example, there is not BMC hardware on
    the node.

    """

    def __init__(self):
        pass

    #def init_host(self, host):
    #    """Initialize anything that is necessary for the driver."""
    #    raise NotImplementedError()
