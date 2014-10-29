#!/usr/bin/env python
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

"""Starter script for Vsm Hardware."""

import eventlet
eventlet.monkey_patch()

import os
import sys
from oslo.config import cfg

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'vsm', '__init__.py')):
    sys.path.insert(0, possible_topdir)

from vsm import flags
from vsm.openstack.common import log as logging
from vsm import service
from vsm import utils

FLAGS = flags.FLAGS

if __name__ == '__main__':
    flags.parse_args(sys.argv)
    logging.setup("vsm")
    utils.monkey_patch()
    launcher = service.ProcessLauncher()
    server = service.Service.create(binary='vsm-testdb')
    launcher.launch_server(server)
    launcher.wait()
