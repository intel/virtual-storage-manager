# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel Inc.
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

"""The storage_pools api."""

import uuid
import webob
from webob import exc
import re

from vsm.api import common
from vsm.api.openstack import wsgi
from vsm.api import xmlutil
from vsm import exception
from vsm import flags
from vsm.openstack.common import log as logging
from vsm.api.views import pools as pools_views
from vsm.openstack.common import jsonutils
from vsm import db
from vsm import utils
from vsm import conductor
from vsm import scheduler

LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS

def _translate_attachment_detail_view(_context, vol):
    """Maps keys for attachment details view."""

    d = _translate_attachment_summary_view(_context, vol)

    # No additional data / lookups at the moment

    return d

def _translate_attachment_summary_view(_context, vol):
    """Maps keys for attachment summary view."""
    d = {}

    storage_pool_id = vol['id']

# NOTE(justinsb): We use the storage_pool id as the id of the attachment object
    d['id'] = storage_pool_id

    d['storage_pool_id'] = storage_pool_id
    d['server_id'] = vol['instance_uuid']
    if vol.get('mountpoint'):
        d['device'] = vol['mountpoint']

    return d

def _translate_storage_pool_detail_view(context, vol, image_id=None):
    """Maps keys for storage_pools details view."""

    d = _translate_storage_pool_summary_view(context, vol, image_id)

    # No additional data / lookups at the moment

    return d

def _translate_storage_pool_summary_view(context, vol, image_id=None):
    """Maps keys for storage_pools summary view."""
    d = {}

    d['id'] = vol['id']
    d['status'] = vol['status']
    d['size'] = vol['size']
    d['availability_zone'] = vol['availability_zone']
    d['created_at'] = vol['created_at']

    d['attachments'] = []
    if vol['attach_status'] == 'attached':
        attachment = _translate_attachment_detail_view(context, vol)
        d['attachments'].append(attachment)

    d['display_name'] = vol['display_name']
    d['display_description'] = vol['display_description']

    if vol['storage_pool_type_id'] and vol.get('storage_pool_type'):
        d['storage_pool_type'] = vol['storage_pool_type']['name']
    else:
        # TODO(bcwaldon): remove str cast once we use uuids
        d['storage_pool_type'] = str(vol['storage_pool_type_id'])

    d['snapshot_id'] = vol['snapshot_id']
    d['source_volid'] = vol['source_volid']

    if image_id:
        d['image_id'] = image_id

    LOG.audit(_("vol=%s"), vol, context=context)

    if vol.get('storage_pool_metadata'):
        metadata = vol.get('storage_pool_metadata')
        d['metadata'] = dict((item['key'], item['value']) for item in metadata)
    # avoid circular ref when vol is a StoragePool instance
    elif vol.get('metadata') and isinstance(vol.get('metadata'), dict):
        d['metadata'] = vol['metadata']
    else:
        d['metadata'] = {}

    if vol.get('storage_pool_glance_metadata'):
        d['bootable'] = 'true'
    else:
        d['bootable'] = 'false'

    return d

def make_attachment(elem):
    elem.set('id')
    elem.set('server_id')
    elem.set('storage_pool_id')
    elem.set('device')

def make_storage_pool(elem):
    elem.set('id')
    elem.set('status')
    elem.set('size')
    elem.set('availability_zone')
    elem.set('created_at')
    elem.set('display_name')
    elem.set('display_description')
    elem.set('storage_pool_type')
    elem.set('snapshot_id')
    elem.set('source_volid')

    attachments = xmlutil.SubTemplateElement(elem, 'attachments')
    attachment = xmlutil.SubTemplateElement(attachments, 'attachment',
                                            selector='attachments')
    make_attachment(attachment)

    # Attach metadata node
    elem.append(common.MetadataTemplate())

storage_pool_nsmap = {None: xmlutil.XMLNS_VOLUME_V1, 'atom': xmlutil.XMLNS_ATOM}

class StoragePoolTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storage_pool', selector='storage_pool')
        make_storage_pool(root)
        return xmlutil.MasterTemplate(root, 1, nsmap=storage_pool_nsmap)

class StoragePoolsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('storage_pools')
        elem = xmlutil.SubTemplateElement(root,
                                            'storage_pool',
                                            selector='storage_pools')
        make_storage_pool(elem)
        return xmlutil.MasterTemplate(root, 1, nsmap=storage_pool_nsmap)

class CommonDeserializer(wsgi.MetadataXMLDeserializer):
    """Common deserializer to handle xml-formatted storage_pool requests.

       Handles standard storage_pool attributes as well as the optional metadata
       attribute
    """

    metadata_deserializer = common.MetadataXMLDeserializer()

    def _extract_storage_pool(self, node):
        """Marshal the storage_pool attribute of a parsed request."""
        storage_pool = {}
        storage_pool_node = self.find_first_child_named(node, 'storage_pool')

        attributes = ['display_name', 'display_description', 'size',
                      'storage_pool_type', 'availability_zone']
        for attr in attributes:
            if storage_pool_node.getAttribute(attr):
                storage_pool[attr] = storage_pool_node.getAttribute(attr)

        metadata_node = self.find_first_child_named(storage_pool_node,
                                                    'metadata')
        if metadata_node is not None:
            storage_pool['metadata'] = self.extract_metadata(metadata_node)

        return storage_pool

class CreateDeserializer(CommonDeserializer):
    """Deserializer to handle xml-formatted create storage_pool requests.lder
       handles standard storage_pool attributes as well as the optional metadata
       attribute
    """

    def default(self, string):
        """Deserialize an xml-formatted storage_pool create request."""
        dom = utils.safe_minidom_parse_string(string)
        storage_pool = self._extract_storage_pool(dom)
        return {'body': {'storage_pool': storage_pool}}

class StoragePoolController(wsgi.Controller):
    """The StoragePools API controller for the OpenStack API."""
    _view_builder_class = pools_views.ViewBuilder

    def __init__(self, ext_mgr):
        self.conductor_api = conductor.API()
        self.scheduler_api = scheduler.API()
        self.ext_mgr = ext_mgr
        
        # at this point, we will add the map as an data member 
        # about storage_group and pool_size
        #self.group_map = scheduler_api.

        super(StoragePoolController, self).__init__()

    @wsgi.serializers(xml=StoragePoolTemplate)
    def show(self, req, id):
        """ Return data about the given storage pool """

        context = req.environ['vsm.context']

        try:
            storage_pool = self.conductor_api.get_storage_pool(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return {"pool": storage_pool}

    def delete(self, req, id):
        """Delete a storage_pool."""
        context = req.environ['vsm.context']

        LOG.audit(_("Delete storage_pool with id: %s"), id, context=context)

        try:
            storage_pool = self.conductor_api.get(context, id)
            self.conductor_api.delete(context, storage_pool)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        return webob.Response(status_int=202)

    @wsgi.serializers(xml=StoragePoolsTemplate)
    def index(self, req):
        """Returns a summary list of storage_pools."""
        return self._items(req,
                            entity_maker=_translate_storage_pool_summary_view)

    @wsgi.serializers(xml=StoragePoolsTemplate)
    def test_scheduler(self, req, body=None):
        """Returns a detailed list of host status."""
        body_info = body.get('request', None)
        search_opts = {}
        search_opts.update(req.GET)

        context = req.environ['vsm.context']
        remove_invalid_options(context,
                                search_opts, 
                                self._get_storage_pool_search_options)

        res = self.scheduler_api.test_service(context, body_info)
        return {'key': res}

    @wsgi.serializers(xml=StoragePoolsTemplate)
    def create(self, req, body=None):
        """Create a storage pool."""
        LOG.info(body)

        #{'pool':
        #    {'replicationFactor': 3,
        #    'name': 'test',
        #    'enablePoolQuota': False,
        #    'storageGroupId': '1',
        #    'u'replicatedStorageGroupId': '1',
        #    'clusterId': '0',
        #    'tag': 'abc',
        #    'createdBy': 'VSM',
        #    'ecProfileId': '1',
        #    'ecFailureDomain': 'osd',
        #    'poolQuota': 0
        #    }
        #}

        if not self.is_valid_body(body, 'pool'):
            raise exc.HTTPUnprocessableEntity()

        context = req.environ['vsm.context']
        pool_dict = body['pool']

        for key in ('name', 'createdBy', 'storageGroupName'):
            if not key in pool_dict:
                msg = _("%s is not defined in pool" % key)
                raise exc.HTTPBadRequest(explanation=msg)

        name = pool_dict['name'].strip()
        created_by = pool_dict['createdBy'].strip()

        storage_group_name = pool_dict['storageGroupName']
        tag = pool_dict['tag'].strip()
        cluster_id = pool_dict['clusterId']

        try:
            cluster_id = int(str(cluster_id))
        except ValueError:
            msg = _('cluster_id must be an interger value')
            raise exc.HTTPBadRequest(explanation=msg)

        storage_group = db.storage_group_get_by_name(context, storage_group_name)
        rule_id = storage_group['rule_id']
        storage_group_id =  storage_group['id']
        size = db.get_size_by_storage_group_name(context,storage_group_name)
        size = int(size)
        if size == 0:
            pool_default_size = db.vsm_settings_get_by_name(context,'osd_pool_default_size')
            size = int(pool_default_size.value)
        #LOG.info('size=====%s'%size)
        #osd_num = 2 #TODO self.scheduler_api.get_osd_num_from_crushmap_by_rule(context, rule_id)
        is_ec_pool = pool_dict.get('ecProfileId')
        if is_ec_pool:
            #erasure code pool 
            body_info = {'name': name,
                        'cluster_id':cluster_id,
                        'storage_group_id':storage_group_id,
                        'storage_group_name':storage_group_name,
                        'ec_profile_id':pool_dict['ecProfileId'],
                        'ec_ruleset_root':storage_group['name'],
                        'ec_failure_domain':pool_dict['ecFailureDomain'],
                        'created_by':created_by,
                        'tag':tag}
             
        else:
            #replicated pool 
            crush_ruleset = rule_id#self.conductor_api.get_ruleset_id(context, storage_group_id)
            if crush_ruleset < 0:
                msg = _('crush_ruleset must be a non-negative integer value')
                raise exc.HTTPBadRequest(explanation=msg)

            #size = pool_dict['replicationFactor']
            #replica_storage_group_id = pool_dict['replicatedStorageGroupId']
            #try:
            #     size = int(str(size))
            #     if size < 1:
            #         msg = _('size must be > 1')
            #         raise exc.HTTPBadRequest(explanation=msg)
            #
            #     host_num = self.conductor_api.count_hosts_by_storage_group_id(context, storage_group_id)
            #     LOG.info("storage_group_id:%s,host_num:%s", storage_group_id, host_num)
            #     if size > host_num:
            #         msg = "The replication factor must be less than or equal to the number of storage nodes in the specific storage group in cluster!"
            #         return {'message': msg}
            # except ValueError:
            #     msg = _('size must be an interger value')
            #     raise exc.HTTPBadRequest(explanation=msg)

            #pg_num = self._compute_pg_num(context, osd_num, size)

            #vsm_id = str(uuid.uuid1()).split('-')[0]
            pg_num = pool_dict.get('pg_num', 64)
            #self._compute_pg_num(context, osd_num, size)
            body_info = {'name': name, #+ "-vsm" + vsm_id,
                        'cluster_id':cluster_id,
                        'storage_group_id':storage_group_id,
                        'storage_group_name':storage_group_name,
                        'pool_type':'replicated',
                        'crush_ruleset':crush_ruleset,
                        'pg_num':pg_num,
                        'pgp_num':pg_num,
                        'size':size,
                        'min_size':size,
                        'created_by':created_by,
                        'tag':tag}

        body_info.update({
            "quota": pool_dict.get("poolQuota"),
            "enable_quota": pool_dict.get("enablePoolQuota"),
            "max_pg_num_per_osd": pool_dict.get("max_pg_num_per_osd") or 100,
            "auto_growth_pg": pool_dict.get("auto_growth_pg") or 0,
        })
        #LOG.info('body_info=====%s'%body_info)
        return self.scheduler_api.create_storage_pool(context, body_info)

    @wsgi.serializers(xml=StoragePoolsTemplate)
    def add_cache_tier(self, req, body=None):
        """add a cache tier."""
        LOG.info(body)

        #{'cache_tier':
        #    {'storage_pool_id': 3,
        #    'cache_pool_id': 4,
        #    'cache_mode': 'writeback',
        #    }
        #}

        if not self.is_valid_body(body, 'cache_tier'):
            raise exc.HTTPUnprocessableEntity()

        context = req.environ['vsm.context']
        cache_tier_body = body['cache_tier']
        return self.scheduler_api.add_cache_tier(context, cache_tier_body)

    @wsgi.serializers(xml=StoragePoolsTemplate)
    def remove_cache_tier(self, req, body=None):
        """add a cache tier."""
        LOG.info(body)

        #{'cache_tier':
        #    {
        #    'cache_pool_id': 4,
        #    }
        #}

        if not self.is_valid_body(body, 'cache_tier'):
            raise exc.HTTPUnprocessableEntity()

        context = req.environ['vsm.context']
        cache_tier_body = body['cache_tier']
        return self.scheduler_api.remove_cache_tier(context, cache_tier_body)

    @wsgi.serializers(xml=StoragePoolsTemplate)
    def get_storage_group_list(self, req):
        """storage_group_list."""
        context = req.environ['vsm.context']
        storage_group_list = self.scheduler_api.get_storage_group_list(context)
        return storage_group_list

    @wsgi.serializers(xml=StoragePoolsTemplate)
    def get_ec_profile_list(self, req):
        """ec_profile_list."""
        context = req.environ['vsm.context']
        ec_profile_list = db.ec_profile_get_all(context)
        ec_profiles = {"ec_profiles": [{"id": x.id, "name": x.name} for x in ec_profile_list]}
        return ec_profiles

    @wsgi.serializers(xml=StoragePoolsTemplate)
    def list_storage_pool(self, req):
        """List storage pools."""
        """TODO: the func is deprecated. plz use detail()."""
        search_opts = {}
        search_opts.update(req.GET)
        context = req.environ['vsm.context']
        remove_invalid_options(context,
                                search_opts,
                                self._get_storage_pool_search_options)

        pools = self.conductor_api.list_storage_pool(context)
        pool_list = pools.values()
        sorted_pools = sorted(pool_list,
                              key=lambda item: item['id'])
        LOG.info('vsm/api/v1/storage_pool.py list_storage_pool')
        #mapping = self.conductor_api.get_mapping(context)

        #LOG.info("api:sorted_pools:%s" % sorted_pools)

        return self._view_builder.detail(sorted_pools)

    @wsgi.serializers(xml=StoragePoolsTemplate)
    def resource_info(self, req, body=None):
        """Returns a detailed list of host status."""
        body_info = body.get('request', None)
        search_opts = {}
        search_opts.update(req.GET)

        context = req.environ['vsm.context']
        remove_invalid_options(context,
                                search_opts,
                                self._get_storage_pool_search_options)

        res = self.conductor_api.resource_info(context)
        LOG.info(' API return value')
        LOG.info(res)
        return {'resource_info': res}

    @wsgi.serializers(xml=StoragePoolsTemplate)
    def detail(self, req):
        """Returns a detailed list of storage_pools."""

        """List storage pools."""
        search_opts = {}
        search_opts.update(req.GET)
        context = req.environ['vsm.context']
        remove_invalid_options(context,
                                search_opts,
                                self._get_storage_pool_search_options)

        pools = self.conductor_api.list_storage_pool(context)
        pool_list = pools.values()
        sorted_pools = sorted(pool_list,
                              key=lambda item: item['id'])
        LOG.info('vsm/api/v1/storage_pool.py list_storage_pool')
        #mapping = self.conductor_api.get_mapping(context)

        return self._view_builder.detail(sorted_pools)
        #
        #LOG.debug(' comes to detail')
        #return self._items(req,
        #                    entity_maker=_translate_storage_pool_detail_view)

    def _compute_pg_num(self, context, osd_num, replication_num):
        """compute pg_num"""
        try:
            pg_count_factor = 200
            settings = db.vsm_settings_get_all(context)
            for setting in settings:
                if setting['name'] == 'pg_count_factor':
                    pg_count_factor = int(setting['value'])
            
            pg_num = pg_count_factor * osd_num//replication_num
        except ZeroDivisionError,e:
            raise exc.HTTPBadRequest(explanation=str(e))
        if pg_num < 1:
            msg = _("Could not compute proper pg_num.")
            raise exc.HTTPBadRequest(explanation=msg)
        return pg_num

    def _items(self, req, entity_maker):
        """Returns a list of storage_pools, transformed through entity_maker."""

        LOG.info(req)
        search_opts = {}
        search_opts.update(req.GET)

        context = req.environ['vsm.context']
        remove_invalid_options(context,
                                search_opts,
                                self._get_storage_pool_search_options())

        res = self.conductor_api.test_service(context)
        return {'pool': res}

    def _get_storage_pool_search_options(self):
        """Return storage_pool search options allowed by non-admin."""
        return ('display_name', 'status')

    @wsgi.serializers(xml=StoragePoolTemplate)
    def update(self, req, id, body):
        """Update a storage_pool."""
        context = req.environ['vsm.context']

        if not body:
            raise exc.HTTPUnprocessableEntity()

        if 'storage_pool' not in body:
            raise exc.HTTPUnprocessableEntity()

        storage_pool = body['storage_pool']
        update_dict = {}

        valid_update_keys = (
            'display_name',
            'display_description',
            'metadata',
        )

        for key in valid_update_keys:
            if key in storage_pool:
                update_dict[key] = storage_pool[key]

        try:
            storage_pool = self.conductor_api.get(context, id)
            self.conductor_api.update(context, storage_pool, update_dict)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        storage_pool.update(update_dict)

        return {'storage_pool':
                _translate_storage_pool_detail_view(context, 
                                                    storage_pool)}

def create_resource(ext_mgr):
    return wsgi.Resource(StoragePoolController(ext_mgr))

def remove_invalid_options(context, search_options, allowed_search_options):
    """Remove search options that are not valid for non-admin API/context."""
    if context.is_admin:
        # Allow all options
        return
    # Otherwise, strip out all unknown options
    unknown_options = [opt for opt in search_options
                       if opt not in allowed_search_options]
    bad_options = ", ".join(unknown_options)
    log_msg = _("Removing options '%(bad_options)s' from query") % locals()
    LOG.debug(log_msg)
    for opt in unknown_options:
        del search_options[opt]
