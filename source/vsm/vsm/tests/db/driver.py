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
Drivers for testdbs.

"""

import os
import socket
import time
import re
import string
import atexit

from oslo.config import cfg
from vsm import db
from vsm import exception
from vsm.image import image_utils
from vsm.openstack.common import log as logging
from vsm import utils
from vsm.conductor import rpcapi as conductor_rpcapi

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

class TestDBDriver(object):
    """Executes commands relating to TestDBs."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        pass

    def init_host(self, host):
        pass

    def service_get_all(self, context):
        service_list = db.service_get_all(context)
        for x in service_list:
            LOG.debug('x.id = %s' % x.id)
            LOG.debug('x.topic = %s' % x.topic)
            LOG.debug('x.recipeId = %s' % x.recipe_Id)

class TestPoolDriver(object):
    """Executes commands relating to pool table."""
    def __init__(self, *args, **kwargs):
        pass

    def storage_pool_get_all(self, context):
        pool_list = db.pool_get_all(context)
        LOG.info('Pools: %s' % pool_list)
        for x in pool_list:
            LOG.debug('x.id = %s' % x.id)
            LOG.debug('x.name = %s' % x.name)
            LOG.debug('x.ruleset = %s' % x.ruleset)
        return pool_list

    def storage_pool_update(self, context, pool_id, values):
        db.pool_update(context, pool_id, values)

class TestOsdDriver(object):
    """Execute command relation with Osd table."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        pass

    def init_host(self, host):
        pass
    
    def osd_get_all(self, context):
        LOG.debug("DEBUG test osd_get_all func")
        osd_list = db.osd_state_get_all(context)
        len = osd_list.__len__()
        LOG.debug(len)
        for x in osd_list:
            LOG.debug('x.id = %s' % x.id)
            LOG.debug('x.osd_name = %s' % x.osd_name)
            LOG.debug('x.state = %s' % x.state)
            LOG.debug('x.service_id = %s' % x.service_id)
            LOG.debug('x.device_id = %s' % x.device_id)
            LOG.debug('x.device.total_capacity = %s' % x.device.total_capacity_kb)
        return osd_list
        
    def osd_get_all_down(self, context):
        LOG.debug("DEBUG test osd_get_all_down func")
        osd_list = db.osd_get_all_down(context)
        for x in osd_list:
            LOG.debug('x.id = %s' % x.id)
            LOG.debug('x.osd_name = %s' % x.osd_name)
            LOG.debug('x.state = %s' % x.state)
            LOG.debug('x.service_id = %s' % x.service_id)
            LOG.debug('x.device_id = %s' % x.device_id)
    
    def osd_get_all_up(self, context):
        LOG.debug("DEBUG test osd_get_all_down func")
        osd_list = db.osd_get_all_up(context)
        for x in osd_list:
            LOG.debug('x.id = %s' % x.id)
            LOG.debug('x.osd_name = %s' % x.osd_name)
            LOG.debug('x.state = %s' % x.state)
            LOG.debug('x.service_id = %s' % x.service_id)
            LOG.debug('x.device_id = %s' % x.device_id)
    
    def osd_get_by_service_id(self, context, service_id):
        LOG.debug("DEBUG test osd_get_by_service_id func")
        osd_list = db.osd_get_by_service_id(context, service_id)
        for x in osd_list:
            LOG.debug('x.id = %s' % x.id)
            LOG.debug('x.osd_name = %s' % x.osd_name)
            LOG.debug('x.state = %s' % x.state)
            LOG.debug('x.service_id = %s' % x.service_id)
            LOG.debug('x.device_id = %s' % x.device_id)
    
    def osd_get_by_cluster_id(self, context, cluster_id):
        LOG.debug("DEBUG test osd_get_by_cluster_id func")
        osd_list = db.osd_get_by_cluster_id(context, cluster_id)
        for x in osd_list:
            LOG.debug('x.id = %s' % x.id)
            LOG.debug('x.osd_name = %s' % x.osd_name)
            LOG.debug('x.state = %s' % x.state)
            LOG.debug('x.service_id = %s' % x.service_id)
            LOG.debug('x.device_id = %s' % x.device_id)
 
    def osd_get(self, context, id):
        LOG.debug("DEBUG test osd_get func")
        osd_list = db.osd_get(context, id)
        #len = osd_list.__len__()
        #LOG.debug(len)
        print osd_list
        for x in osd_list:
            print(x)
    
    def osd_destroy(self, context):
        LOG.debug("DEBUG test osd_destroy func")
        db.osd_destroy(context)
 
    def osd_create(self, context, values):
        LOG.debug("DEBUG test osd_create func")
        db.osd_create(context, values)

    def osd_update(self, context, osd_id, values):
        LOG.debug("DEBUG test osd_update func")
        db.osd_update(context, osd_id, values)

    def osd_delete(self, context, osd_id):
        LOG.debug("DEBUG test osd_delete func")
        db.osd_delete(context, osd_id)

class TestCrushMapDriver(object):
    """Execute command relation with CRUSH map table."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        pass

    def init_host(self, host):
        pass
    
    def crushmap_create(self, context, values):
        LOG.debug("DEBUG test crushmap_create func")
        db.crushmap_create(context, values)

    def crushmap_get_all(self, context):
        LOG.debug("DEBUG test crushmap_get_all func")
        crushmap_list = db.crushmap_get_all(context)
        for x in crushmap_list:
            LOG.debug("crushmap id = %s" % x.id)
            LOG.debug("crushmap content = %s" % x.content)
            LOG.debug("crushmap created_at = %s" % x.created_at)
            LOG.debug("crushmap deleted = %s" % x.deleted)
    
    def crushmap_get(self, context, crushmap_id):
        LOG.debug("DEBUG test crushmap_get func")
        crushmap_list = db.crushmap_get(context, crushmap_id)
        for x in crushmap_list:
            print x

    def crushmap_update(self, context, crushmap_id, values):
        LOG.debug("DEBUG test crushmap_update func")
        db.crushmap_update(context, crushmap_id, values)

    def crushmap_delete(self, context, crushmap_id):
        LOG.debug("DEBUG test crushmap_delete func")
        db.crushmap_delete(context, crushmap_id)

class TestServiceDriver(object):
    """Execute command relation with services table."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        pass

    def init_host(self, host):
        pass

    def service_create(self, context, values):
        LOG.debug("DEBUG test service_create func")
        db.service_create(context, values)

    def service_get_all(self, context, disabled=None):
        LOG.debug("DEBUG test service_get_all func")
        service_list = db.service_get_all(context)
        for x in service_list:
            LOG.debug("service id = %s" % x.id)
            LOG.debug("service host = %s" % x.host)
            LOG.debug("service binary = %s" % x.binary)
            LOG.debug("service topic = %s" % x.topic)
            LOG.debug("service report_count = %s" % x.report_count)
            LOG.debug("service created_at = %s" % x.created_at)

    def service_get(self, context, service_id):
        LOG.debug("DEBUG test service_get func")
        service_list = db.service_get(context, service_id)
        for x in service_list:
            print(x)

    def service_update(self, context, service_id, values):
        LOG.debug("DEBUG test service_update func")
        db.service_update(context, service_id, values)

class TestDeviceDriver(object):
    """Execute command relation with devices table."""
    def __init__(self, execute=utils.execute, *args, **kwargs):
        pass

    def init_host(self, host):
        pass
    
    def device_create(self, context, values):
        LOG.debug("DEBUG test device_create func")
        device_list = db.device_create(context, values)
    
    def device_get_all_by_interface_type(self, context, interface_type):
        LOG.debug("DEBUG test device_get_all_by_interface_type func")
        device_list = db.device_get_all_by_interface_type(context, interface_type)
        print(device_list)
        for x in device_list:
            LOG.debug("device id = %s" % x.id)
            LOG.debug("device name = %s" % x.name)
            LOG.debug("service id = %s" % x.service_id)
            LOG.debug("device device type = %s" % x.device_type)
            LOG.debug("device interface type = %s" % x.interface_type)
            LOG.debug("device device state = %s" % x.state)
    
    def device_get_all_by_device_type(self, context, device_type):
        LOG.debug("DEBUG test device_get_all_by_device_type func")
        device_list = db.device_get_all_by_device_type(context, device_type)
        for x in device_list:
            LOG.debug("device id = %s" % x.id)
            LOG.debug("device name = %s" % x.name)
            LOG.debug("service id = %s" % x.service_id)
            LOG.debug("device device type = %s" % x.device_type)
            LOG.debug("device interface type = %s" % x.interface_type)
            LOG.debug("device device state = %s" % x.state)

class TestSummaryDriver(object):
    """ create and update summary table"""
    def __init__(self, *args, **kwargs):
        pass

    def create_summary(self, context, values):
        LOG.debug('create summary. ')
        summary = db.summary_create(context, values)
        return summary

    def update_summary(self, context, cluster_id, typ, values):
        LOG.debug('update summary. ')
        summary = db.summary_update(context, cluster_id, typ, values)
        return summary

    def get_summary_by_id_and_type(self, context, cluster_id, typ):
        LOG.debug('get summary. ')
        summary = db.summary_get_by_cluster_id_and_type(context, cluster_id, typ)
        return summary

class TestMonDriver(object):
    """ create and update monitors table"""
    def __init__(self, *args, **kwargs):
        pass

    def get_all_monitors(self, context):
        return db.monitor_get_all(context)

    def update_monitor(self, context, mon_name, values):
        LOG.debug('create/update monitor. ')
        mon = db.monitor_update(context, mon_name, values)
        return mon

class TestPGDriver(object):
    def __init__(self, *args, **kwargs):
        self._conductor_rpcapi = conductor_rpcapi.ConductorAPI()

    def pg_create(self, context, values):
        return db.pg_create(context, values)

    def pg_update(self, context, pg_id, values):
        return db.pg_update(context, pg_id, values)

    def pg_get_all(self, context):
        return self._conductor_rpcapi.pg_get_all(context)

    def pg_update_or_create(self, context, values):
        return self._conductor_rpcapi.pg_update_or_create(context, values)

class TestRbdDriver(object):
    def __init__(self, *args, **kwargs):
        self._conductor_rpcapi = conductor_rpcapi.ConductorAPI()

    def rbd_create(self, context, values):
        return db.rbd_create(context, values)

    def rbd_update(self, context, rbd_id, values):
        return db.rbd_update(context, rbd_id, values)

    def rbd_get_all(self, context):
        return db.rbd_get_all(context)

    def rbd_update_or_create(self, context, values):
        return db.rbd_update_or_create(context, values)

class TestSettingDriver(object):
    def __init__(self):
        pass

    def setting_create(self, context, values):
        return db.vsm_settings_update_or_create(context, values)

    def setting_update(self, context, values):
        return db.vsm_settings_update_or_create(context, values)

    def settings_get_all(self, context):
        return db.vsm_settings_get_all(context)

    def settings_get_by_name(self, context, name):
        return db.vsm_settings_get_by_name(context, name)
