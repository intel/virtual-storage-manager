# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Inc.
# All Rights Reserved.

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

import webob
from webob import exc
from vsm.api.openstack import wsgi
from vsm.api import xmlutil
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.api.views import storage_groups as storage_group_views
from vsm import conductor
from vsm import scheduler
from vsm import exception
from vsm import db

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def make_storage_group(elem, detailed=False):
    elem.set('id')
    elem.set('name')
    elem.set('address')
    elem.set('health')
    elem.set('detail')
    elem.set('skew')
    elem.set('latency')
    elem.set('kb_total')
    elem.set('kb_used')
    elem.set('kb_avail')
    elem.set('percent_avail')

    if detailed:
        pass

storage_group_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}

class StorageGroupTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storage_group', selector='storage_group')
        make_storage_group(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=storage_group_nsmap)

class StorageGroupsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storage_groups')
        elem = xmlutil.SubTemplateElement(root, 'storage_group', selector='storage_groupss')
        make_storage_group(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=storage_group_nsmap)

class Controller(wsgi.Controller):
    """The storage_groups API controller for the OpenStack API."""
    _view_builder_class = storage_group_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        super(Controller, self).__init__()

    #def _get_zone_search_options(self):
    #    """Return zone search options allowed by non-admin."""
    #    return ('id', 'name', 'public_ip')

    def _get_storage_group(self, context, req, id):
        """Utility function for looking up an instance by id."""
        try:
            storage_group = self.conductor_api.storage_group_get(context, id)
        except exception.NotFound:
            msg = _("storage_group could not be found")
            raise exc.HTTPNotFound(explanation=msg)
        return storage_group

    @wsgi.serializers(xml=StorageGroupTemplate)
    def create(self, req, body):
        """create zone."""
        LOG.info("CEPH_LOG storage group create body: %s" % body)
        context = req.environ['vsm.context']
        storage_group = body['storage_group']
        storage_group.update({"rule_id": -1})
        db.create_storage_group(context, storage_group)
        #self.scheduler_api.add_new_zone(context, body)
        return webob.Response(status_int=202)

    def create_with_takes(self, req, body=None):
        '''

        :param res:
        :param body:
        :return:
        '''
        LOG.info("CEPH_LOG create_with_takes body=%s"%body )
        context = req.environ['vsm.context']
        ret = self.scheduler_api.add_storage_group_to_crushmap_and_db(context,body)
        LOG.info('CEPH_LOG create_with_takes  ret=%s'%ret)
        return ret

    def update_with_takes(self, req, body=None):
        '''

        :param res:
        :param body:
        :return:
        '''
        LOG.info("CEPH_LOG update_with_takes body=%s"%body )
        context = req.environ['vsm.context']
        ret = self.scheduler_api.update_storage_group_to_crushmap_and_db(context,body)
        LOG.info('CEPH_LOG update_with_takes  ret=%s'%ret)
        return ret

    @wsgi.serializers(xml=StorageGroupsTemplate)
    def show(self, req, id):
        """Return data about the given storage_group."""
        context = req.environ['vsm.context']

        try:
            storage_group = self._get_storage_group(context, req, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return {'storage_group': storage_group}

    @wsgi.serializers(xml=StorageGroupsTemplate)
    def index(self, req):
        """Get storage_group list."""
        #search_opts = {}
        #search_opts.update(req.GET)
        context = req.environ['vsm.context']
        #remove_invalid_options(context,
        #                        search_opts,
        #                        self._get_zone_search_options)
        #zones = self.conductor_api.get_zone_list(context)
        storage_groups = [{}, {}]
        LOG.info('vsm/api/v1/storage_group.py storage_groups:%s' % storage_groups)

        return self._view_builder.index(req, storage_groups)

    @wsgi.serializers(xml=StorageGroupsTemplate)
    def detail(self, req):

        """Get storage_group list."""
        context = req.environ['vsm.context']
        storage_groups_db = self.conductor_api.storage_group_get_all(context)
        storage_groups = {}
        storage_group_name_list = []
        for storage_group_db in storage_groups_db:
            take_dict = {
                "id":storage_group_db['take_id'],
                "name":"",
                "order":storage_group_db['take_order'],
                "choose_type":storage_group_db['choose_type'],
                "choose_num":storage_group_db['choose_num']
            }
            if storage_group_db['take_id']:
                try:
                    take_dict['name'] = db.zone_get(context,storage_group_db['take_id'])['name']
                except:
                    self.scheduler_api.update_zones_from_crushmap_to_db(context)
                    take_dict['name'] = db.zone_get(context,storage_group_db['take_id'])['name']

            if storage_group_db['name'] in storage_group_name_list:
                storage_groups[storage_group_db['name']]['take_list'].append(take_dict)
            else:
                storage_group_name_list.append(storage_group_db['name'])
                storage_group_dict = {
                    'id':storage_group_db['id'],
                    'name':storage_group_db['name'],
                    'storage_class':storage_group_db['storage_class'],
                    'friendly_name':storage_group_db['friendly_name'],
                    'marker':storage_group_db['marker'],
                    'rule_id':storage_group_db['rule_id'],
                    'take_list':[take_dict],
                    'status': storage_group_db["status"],
                }
                storage_groups[storage_group_db['name']] = storage_group_dict

        storage_groups = storage_groups.values()

        LOG.info('vsm/api/v1/storage_groups.py detailed storage_groups:%s' % storage_groups)
        osds = self.conductor_api.osd_state_get_all(context)
        LOG.info('vsm/api/v1/storage_groups.py detailed osds:%s' % osds)
        sp_usages = db.get_storage_pool_usage(context)
        LOG.info('vsm/api/v1/storage_groups.py detailed sp usage:%s' % sp_usages)
        pools = self.conductor_api.list_storage_pool(context)
        LOG.info('vsm/api/v1/storage_groups.py detailed pools:%s' % pools)
        LOG.info('vsm/api/v1/storage_groups.py detailed pools:%s' % type(pools))
        for sp_usage in sp_usages:
            pool_id = str(sp_usage['pool_id'])
            if pool_id in pools:
                pools[pool_id]['attach_status'] = sp_usage['attach_status']

        rules = [storage_group['name'] for storage_group in storage_groups]
        rules_dict = {'rules':list(set(rules))}
        rule_osds = self.scheduler_api.get_osds_by_rules(context,rules_dict )
        for storage_group in storage_groups:
            osds_in_storage_group = rule_osds.get(storage_group['name'])#osd['storage_group']['id'] == storage_group["id"]]
            osd_cnt = len(osds_in_storage_group)
            storage_group['capacity_total'] = sum([osd["device"]['total_capacity_kb'] for osd in osds
                                               if osd['osd_name'] in osds_in_storage_group])
            storage_group['capacity_used'] = sum([osd["device"]['used_capacity_kb'] for osd in osds
                                               if osd['osd_name'] in osds_in_storage_group])
            storage_group['capacity_avail'] = sum([osd["device"]['avail_capacity_kb'] for osd in osds
                                               if osd['osd_name'] in osds_in_storage_group])

            nodes = {}
            #osd_cnt = 0
            for osd in osds:
                if not osd['storage_group']['id'] == storage_group["id"] or osd['state'] == FLAGS.vsm_status_uninitialized:
                    continue
                #osd_cnt = osd_cnt + 1
                k = osd['service']['host']
                if k not in osd:
                    nodes.setdefault(k, 0)
                nodes[k] += osd["device"]['used_capacity_kb']
            if not nodes:
                storage_group['largest_node_capacity_used'] = 0
            else:
                storage_group['largest_node_capacity_used'] = max(nodes.values())

            storage_group["attached_osds"] = osd_cnt
            # attached pools
            storage_group["attached_pools"] = len([pool for pool in pools.values()
                                                    if (pool['primary_storage_group_id'] == storage_group["id"])])
            try:
                storage_group['updated_at'] = osds[0]['updated_at']
            except:
                pass
            LOG.info("vsm/api/v1/storage_groups.py %s" % storage_group)

        return self._view_builder.index(req, storage_groups)

    def summary(self, req, body=None):
        LOG.info('CEPH_LOG storage_group-summary body %s ' % body)
        context = req.environ['vsm.context']
        return {'storage_group-summary':{'epoch': 123,
                               'num_storage_groups': 12,
                               'num_up_storage_groups': 8,
                               'num_in_storage_groups': 8,
                               'nearfull': False,
                               'full': False,
                               }}

    def get_default_pg_num(self, req):
        context = req.environ['vsm.context']
        storage_group_name= req.GET.get('storage_group_name',None)
        LOG.info('CEPH_LOG get_default_pg_num %s ' % storage_group_name)
        body = {'storage_group_name':storage_group_name}
        default_pg_num = self.scheduler_api.get_default_pg_num_by_storage_group(context,body)
        return default_pg_num

def create_resource(ext_mgr):
    return wsgi.Resource(Controller(ext_mgr))

#def remove_invalid_options(context, search_options, allowed_search_options):
#    """Remove search options that are not valid for non-admin API/context."""
#    if context.is_admin:
#        # Allow all options
#        return
#    # Otherwise, strip out all unknown options
#    unknown_options = [opt for opt in search_options
#                       if opt not in allowed_search_options]
#    bad_options = ", ".join(unknown_options)
#    log_msg = _("Removing options '%(bad_options)s' from query") % locals()
#    LOG.debug(log_msg)
#    for opt in unknown_options:
#        del search_options[opt]
