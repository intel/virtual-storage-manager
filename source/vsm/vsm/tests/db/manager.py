# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel.
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
TestDB Service
"""

import os
import json
from oslo.config import cfg
import datetime
from vsm import context
from vsm import db
from vsm import exception
from vsm import flags
from vsm import manager
from vsm import conductor
from vsm.conductor import rpcapi as conductor_rpcapi
from vsm.openstack.common import excutils
from vsm.openstack.common import importutils
from vsm.openstack.common import log as logging
from vsm.openstack.common.notifier import api as notifier
from vsm.openstack.common import timeutils
from vsm.tests.db import driver
from vsm import version

testdb_opts = [
    cfg.StrOpt('testdb_manager',
               default='vsm.tests.db.manager.TestDBManager',
               help='full class name for the Manager for storage backup'),
    cfg.StrOpt('testdb_topic',
               default='vsm-testdb',
               help='the topic testdb nodes listen on'),

]
testdb_group = cfg.OptGroup(name='testdb',
                               title='TestDB Options')
CONF = cfg.CONF
CONF.register_group(testdb_group)
CONF.register_opts(testdb_opts, testdb_group)

LOG = logging.getLogger(__name__)
FLAGS = flags.FLAGS

class TestDBManager(manager.Manager):
    """Chooses a host to create storages."""

    RPC_API_VERSION = '1.2'

    def __init__(self, service_name=None, *args, **kwargs):
        #if not scheduler_driver:
        #    scheduler_driver = FLAGS.scheduler_driver
        #self.driver = importutils.import_object(scheduler_driver)
        super(TestDBManager, self).__init__(*args, **kwargs)
        self._context = context.get_admin_context()
        self._conductor_api = conductor.API()
        #self._driver = driver.TestDBDriver()
        #self._driver.service_get_all(self._context)
        
        """
        Test the code about osdstate table
        self._driver = driver.TestOsdDriver()
        #self._values = {'osd_name':'osd.4', 'device_id':7, 'service_id':3, 'state':'up'}
        #self._driver.osd_create(self._context, self._values)
        ret = self._driver.osd_get_all(self._context)
        LOG.info('osd get all %s' % ret)
        #self._driver.osd_get_by_cluster_id(self._context, 1)
        self._id = 1
        #self._driver.osd_get(self._context, self._id)
        #self._driver.osd_destroy(self._context, self._id)

        #get_info = lambda x: json.loads(os.popen(x + " -f json-pretty").read())
        #ceph_dict = get_info("ssh 10.239.82.186 ceph pg dump osds")
        #
        #self._values = {'total_cap': ceph_dict[0]['kb'],
        #                'used_cap': ceph_dict[0]['kb_used'],
        #                'avail_cap': ceph_dict[0]['kb_avail']}
        #LOG.debug('values: %s', self._values)
        #
        #self._driver.osd_update(self._context, 1, self._values)
        #self._driver.osd_delete(self._context, self._id)
        #self._test_osd_get_all()
        """

        
        """ Test the code about crushmap table.

        self._id = 1
        self._driver = driver.TestCrushMapDriver()
        self._values = {'content':'this is a test modified! second'}
        self._driver.crushmap_create(self._context, self._values)
       #self._driver.crushmap_get_all(self._context)
       #self._driver.crushmap_get(self._context, self._id)
       #self._driver.crushmap_update(self._context, self._id, self._values)
        self._driver.crushmap_delete(self._context, self._id)
        """

        """ Test the function about service.

        self._driver = driver.TestServiceDriver()
        self._values = {'host':'repo_test', 'binary':'conductor_test', 'topic':'conductor_test', 'report_count':11}
        #self._driver.service_create(self._context, self._values)
        #self._driver.service_get_all(self._context)
        self._id = 11
        #self._driver.service_get(self._context, self._id)
        self._values_update = {'deleted':0, 'binary':'test_update'}
        self._driver.service_update(self._context, self._id, self._values_update)
        """

        """Test the function about device

        self._driver = driver.TestDeviceDriver()
        self._values = {'name':'/dev/vdb2', 'service_id':2, 'total_capacity_gb':500,
                        'device_type':'HDD', 'interface_type':'SATA', 'state':'up'}
        #self._driver.device_create(self._context, self._values)
        self._interface_type = "SATA"
        self._driver.device_get_all_by_interface_type(self._context, self._interface_type)
        self._device_type = "SSD"
        self._driver.device_get_all_by_device_type(self._context, self._device_type)
        """

        """ Test Summary
        get_info = lambda x: json.loads(os.popen(x + " -f json-pretty").read())
        ceph_status_dict = get_info("ssh 10.239.82.236 ceph status")
        osd = json.dumps(ceph_status_dict['osdmap'])
        mon_data = {
            'monmap_epoch': ceph_status_dict.get('monmap').get('epoch'),
            'monitors': len(ceph_status_dict.get('monmap').get('mons')),
            'election_epoch': ceph_status_dict.get('election_epoch'),
            'quorum': json.dumps(' '.join(ceph_status_dict.get('quorum_names'))).strip('"'),
            'overall_status': json.dumps(ceph_status_dict.get('health').get('overall_status')).strip('"')
        }
        mds = json.dumps(ceph_status_dict['mdsmap'])
        pg = json.dumps(ceph_status_dict['pgmap'])

        LOG.info('osd summary info %s', osd)
        LOG.info('mon summary info %s', mon_data)

        self._sum_driver = driver.TestSummaryDriver()
        osd_val = {
            'summary_data': osd
        }
        mon_val = {
            'summary_data': json.dumps(mon_data)
        }
        mds_val = {
            'summary_data': mds
        }
        pg_val = {
            'summary_data': pg
        }
        self._sum_driver.update_summary(self._context, 1, 'osd', osd_val)
        self._sum_driver.update_summary(self._context, 1, 'mon', mon_val)
        self._sum_driver.update_summary(self._context, 1, 'mds', mds_val)
        self._sum_driver.update_summary(self._context, 1, 'pg', pg_val)
        #val = {
        #    'summary_data': len(ret.summary_data)
        #}
        #self._driver.update_summary(self._context, ret.cluster_id, ret.summary_type, val)

        for typ in ['osd', 'mon', 'mds', 'pg']:
            ret = self._sum_driver.get_summary_by_id_and_type(self._context, 1, typ)
            LOG.info('-' * 8)
            LOG.info('cluster id: %s', ret.cluster_id)
            LOG.info('type: %s', ret.summary_type)
            LOG.info('data: %s', ret.summary_data)
        """

        """Test Pool
        self._driver = driver.TestPoolDriver()
        pools = self._driver.storage_pool_get_all(self._context)
        pool_ids = [p.get('pool_id') for p in pools]
        LOG.debug('get pool ids : %s', pool_ids)

        get_info = lambda x: json.loads(os.popen(x + " -f json-pretty").read())
        pool_status_dict = get_info("ssh 10.239.82.186 ceph pg dump pools")
        #pool_dict = json.dumps(pool_status_dict)
        pool_io = get_info("ssh 10.239.82.186 ceph osd pool stats")

        for x in pool_status_dict:
            LOG.debug('pool %s' % x)
            if x.get('poolid') in pool_ids:
                self._driver.storage_pool_update(self._context, x.get('poolid'), x.get('stat_sum'))

        for y in pool_io:
            LOG.debug('client io: %s', y)
            if y.get('pool_id') in pool_ids:
                if y.get('client_io_rate'):
                    self._driver.storage_pool_update(self._context, y.get('pool_id'), y.get('client_io_rate'))

        LOG.info(self._driver.storage_pool_get_all(self._context))
        """

        """Test monitors
        self._driver = driver.TestMonDriver()
        #mons = self._driver.get_all_monitors(self._context)

        get_info = lambda x: json.loads(os.popen(x + " -f json-pretty").read())
        health_stat = get_info("ssh 10.239.82.236 ceph health")
        mon_stat = health_stat.get('timechecks').get('mons')

        mon_health = health_stat.get('health').get('health_services')[0].get('mons')
        LOG.debug("mon stat: %s \t\n mon health: %s" %(mon_stat, mon_health))
        #mon_stat_name = [stat.get('name') for stat in mon_stat]
        for health in mon_health:
            for stat in mon_stat:
                if health.get('name') == stat.get('name'):
                    stat.update(health)
                    self._driver.update_monitor(self._context, health.get('name'), stat)

        LOG.info(self._driver.get_all_monitors(self._context))
        """

        """ test pg
        #pg    
        #get_info = lambda x: json.loads(os.popen(x + " -f json-pretty").read())
        #val_list = get_info("ssh 10.239.82.190 ceph pg dump pgs_brief")
        #pg_dict_list = [] 
        #for item in val_list:
        #    dict = {} 
        #    dict['pgid'] = item['pgid']
        #    dict['state'] = item['state']
        #    dict['up'] = ','.join(str(v) for v in item['up'])
        #    dict['acting'] = ','.join(str(v) for v in item['acting'])
        #    pg_dict_list.append(dict)
        #
        #print pg_dict_list
        #self._driver = driver.TestPGDriver()
        #for item in pg_dict_list:
        #    self._driver.pg_create(self._context, item)

        #test get_all
        #self._driver = driver.TestPGDriver()
        #pg_all = self._driver.pg_get_all(self._context)
        #print pg_all

        #test update_or_create
        #get_info = lambda x: json.loads(os.popen(x + " -f json-pretty").read())
        #val_list = get_info("ssh 10.239.82.190 ceph pg dump pgs_brief")
        #pg_dict_list = [] 
        #for item in val_list:
        #    dict = {} 
        #    dict['pgid'] = item['pgid']
        #    dict['state'] = item['state']
        #    dict['up'] = ','.join(str(v) for v in item['up'])
        #    dict['acting'] = ','.join(str(v) for v in item['acting'])
        #    pg_dict_list.append(dict)
        #
        #print pg_dict_list
        #self._driver = driver.TestPGDriver()
        #for item in pg_dict_list:
        #    db.pg_update_or_create(self._context, item)
        """

        """ 
        test rbd
        #rbd

        #test update_or_create
        #get_info = lambda x: json.loads(os.popen(x + " -f json-pretty").read())
        #pool_list = get_info("ssh 10.239.82.190 ceph osd lspools")
        #rbd_list = []
        #for pool in pool_list:
        #    result = os.popen(("rbd ls -l %s --format json --pretty-format") % pool['poolname']).read()
        #    result = "hello"
        #    if result:
        #        #rbd_image_list = json.loads(result)
        #        rbd_image_list = [
        #            { "image": "vmdisk1",
        #              "size": 42949672960,
        #              "format": 1},
        #            { "image": "vmdisk2",
        #              "size": 42949672960,
        #              "format": 1},
        #        ]

        #        for rbd_image in rbd_image_list:
        #            rbd_dict = {} 
        #            #dict = json.loads(os.popen(("rbd --image %s -p %s --pretty-format --format json info") % (rbd_image['image'] , pool['poolname'])).read())
        #            #print dict['objects']
        #            #print dict['order']
        #            rbd_dict['pool'] = pool['poolname']
        #            rbd_dict['image'] = rbd_image['image']
        #            rbd_dict['size'] = rbd_image['size']
        #            rbd_dict['format'] = rbd_image['format']
        #            rbd_dict['objects'] = 10240
        #            rbd_dict['order'] = 22
        #            rbd_list.append(rbd_dict)
        #            db.rbd_update_or_create(self._context, rbd_dict)

        #print rbd_list

        #test get_all
        #rbd = db.rbd_get_all(self._context) 
        #print rbd
        """
        
        """
        # test vsm settings
        #self._driver = driver.TestSettingDriver()
        #values = {
        #    'name': 'vsm2',
        #    'value': 'settings',
        #    'default_value': 'default settings',
        #}
        #
        #ret = db.vsm_settings_update_or_create(self._context, values)
        #if ret:
        #    objs = db.vsm_settings_get_all(self._context)
        #    for obj in objs:
        #        print 'name:%s\t value:%s\n' % (obj.name, obj.value)
        #
        #
        #values['value'] = 'setting again'
        #
        #ret = db.vsm_settings_update_or_create(self._context, values)
        #if ret:
        #    objs = db.vsm_settings_get_all(self._context)
        #    for obj in objs:
        #        print 'name:%s\t value:%s\n' % (obj.name, obj.value)
        """

        """
        test long_call 
#        values = {
#            'uuid':'23456',
#            'status':'ok',
#        }
#        #result = db.long_call_create(self._context,values)
#       
#        uuid = "23456"
#        #result = db.long_call_get_by_uuid(self._context,uuid)
#        result = db.long_call_update(context, uuid, values)
#        #result = db.long_call_delete(context, uuid)
#        LOG.info("WGC %s " % result)
        """

        """
        test get osd count
        """
        #count = db.device_get_count(self._context)
        #LOG.info("count %d" % count)

        #count = db.osd_state_count_service_id_by_storage_group_id(self._context, 1)
        #LOG.info("count:%d" % count)

        #count = db.init_node_count_by_status(self._context, "Stopped")
        #LOG.info("count:%d" % count)
        #values = {'name':'high_performance', 'storage_class':'ssd', 'friendly_name':'High_Performance_SSD', 'rule_id':2, 'drive_extended_threshold':3}
        #db.storage_group_create(self._context, values)
        
        #values = {}
        #values['rule_id'] = 2
        #db.storage_group_update_by_name(self._context, 'high_performance', values)
        

        #osd= self._conductor_api.host_count_by_storage_group(self._context, 'high_performance')
        #LOG.info("count:%s" % osd)
        #osd = self._conductor_api.osd_state_get_all(self._context)
        #LOG.info("osds:%s" % osd)
        #print dir(version) 
        #print version.version_string()
        #print version.release_string()
