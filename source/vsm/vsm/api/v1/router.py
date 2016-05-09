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

"""
WSGI middleware for OpenStack Hardware API.
"""

from vsm.api import extensions
import vsm.api.openstack
from vsm.api.v1 import limits
from vsm.api.v1 import types
from vsm.api import versions
from vsm.api.v1 import conductor
from vsm.api.v1 import storage_pool
from vsm.api.v1 import clusters
from vsm.api.v1 import servers
from vsm.api.v1 import zones
from vsm.api.v1 import agents
from vsm.api.v1 import osds
from vsm.api.v1 import mdses
from vsm.api.v1 import monitors 
from vsm.api.v1 import placement_groups
from vsm.api.v1 import storage_groups
from vsm.api.v1 import rbd_pools
from vsm.api.v1 import devices
from vsm.api.v1 import monitors
from vsm.api.v1 import vsm_settings
from vsm.api.v1 import vsms
from vsm.api.v1 import licenses
from vsm.api.v1 import performance_metrics
from vsm.api.contrib import poolusages
from vsm.api.v1 import ec_profiles
from vsm.api.v1 import rgw

from vsm.openstack.common import log as logging

LOG = logging.getLogger(__name__)

class APIRouter(vsm.api.openstack.APIRouter):
    """
    Routes requests on the OpenStack API to the appropriate controller
    and method.
    """
    ExtensionManager = extensions.ExtensionManager

    def _setup_routes(self, mapper, ext_mgr):
        self.resources['versions'] = versions.create_resource()
        mapper.connect("versions", "/",
                       controller=self.resources['versions'],
                       action='show')

        mapper.redirect("", "/")

        self.resources['types'] = types.create_resource()
        mapper.resource("type", "types",
                        controller=self.resources['types'])

        self.resources['limits'] = limits.create_resource()
        mapper.resource("limit", "limits",
                        controller=self.resources['limits'])

        self.resources['conductor'] = conductor.create_resource(ext_mgr)
        mapper.resource("conductor", "conductor",
                        controller=self.resources['conductor'],
                        collection={'detail': 'get',
                                    'host_status': 'post',
                                    'resource_info':'post',},
                        member={'action': 'post'})

        self.resources['storage_pool'] = storage_pool.create_resource(ext_mgr)
        mapper.resource("storage_pool", "storage_pool",
                        controller=self.resources['storage_pool'],
                        collection={'detail': 'get',
                                    'test_scheduler': 'post',
                                    'resource_info':'post',
                                    'create': 'post',
                                    'get_storage_group_list': 'get',
                                    'get_pool_size_list': 'get',
                                    'list_storage_pool': 'get'},
                        member={'action': 'post'})

        # change name from storage_pool to storage_pools
        self.resources['storage_pools'] = storage_pool.create_resource(ext_mgr)
        mapper.resource("storage_pools", "storage_pools",
                        controller=self.resources['storage_pools'],
                        collection={'detail': 'get',
                                    'test_scheduler': 'post',
                                    'resource_info':'post',
                                    'create': 'post',
                                    'get_storage_group_list': 'get',
                                    'get_pool_size_list': 'get',
                                    'get_ec_profile_list': 'get',
                                    'add_cache_tier': 'post',
                                    'remove_cache_tier': 'post',
                                    'list_storage_pool': 'get'},
                        member={'action': 'post'})

        self.resources['clusters'] = clusters.create_resource(ext_mgr)
        mapper.resource("clusters", "clusters",
                        controller=self.resources['clusters'],
                        collection={'summary': 'get',
                                    'refresh': 'post',
                                    'import_ceph_conf': 'post',
                                    'integrate': 'post',
                                    'start_cluster': 'post',
                                    'stop_cluster': 'post',
                                    'get_ceph_health_list':'get',
                                    'check_pre_existing_cluster':'post',
                                    'import_cluster':'post',
                                    'detect_cephconf':'post',
                                    'detect_crushmap':'post',
                                    'get_crushmap_tree_data':'post',
                                    'get_service_list':'get'
                                    },
                        member={'action': 'post'})

        self.resources['servers'] = servers.create_resource(ext_mgr)
        mapper.resource("servers", "servers",
                        controller=self.resources['servers'],
                        collection={"add": "post",
                                    "remove": "post",
                                    "reset_status": "post",
                                    "start": "post",
                                    "stop": "post",
                                    "ceph_upgrade": "post"},
                        member={'action':'post'})

        self.resources['agents'] = agents.create_resource(ext_mgr)
        mapper.resource("agents", "agents",
                        controller=self.resources['agents'],
                        collection={'detail': 'get'},
                        member={'action':'post'})

        self.resources['zones'] = zones.create_resource(ext_mgr)
        mapper.resource("zones", "zones",
                        controller=self.resources['zones'],
                        collection={'osd_locations_choices': 'get',
                                    'get_zone_not_in_crush_list': 'get',
                                    'add_zone_to_crushmap_and_db': 'post',},
                        member={'action':'POST'})

        self.resources['osds'] = osds.create_resource(ext_mgr)
        mapper.resource("osds", "osds",
                        controller=self.resources['osds'],
                        collection={"summary": "get",
                                    "refresh": "post",
                                    "detail": "get",
                                    "add_batch_new_disks_to_cluster":"post",
                                    "add_new_disks_to_cluster":"post",
                                    "detail_filter_and_sort": "get"},
                        member={'action':'POST'})

        self.resources['mdses'] = mdses.create_resource(ext_mgr)
        mapper.resource("mdses", "mdses",
                        controller=self.resources['mdses'],
                        collection={"summary": "get",
                                    "detail": "get"},
                        member={'action':'POST'})

        self.resources['monitors'] = monitors.create_resource(ext_mgr)
        mapper.resource("monitors", "monitors",
                        controller=self.resources['monitors'],
                        collection={"summary": "get",
                                    "detail": "get"},
                        member={'action':'POST'})

        self.resources['vsms'] = vsms.create_resource(ext_mgr)
        mapper.resource("vsms", "vsms",
                        controller=self.resources['vsms'],
                        collection={"summary": "get"},
                        member={'action':'POST'})

        self.resources['storage_groups'] = storage_groups.create_resource(ext_mgr)
        mapper.resource("storage_groups", "storage_groups",
                        controller=self.resources['storage_groups'],
                        collection={"summary": "get",
                                    "create_with_takes":"post",
                                    "update_with_takes":"post",
                                    "detail": "get",
                                    "get_default_pg_num":"get"},
                        member={'action':'POST'})

        self.resources['placement_groups'] = placement_groups.create_resource(ext_mgr)
        mapper.resource("placement_groups", "placement_groups",
                        controller=self.resources['placement_groups'],
                        collection={"summary": "get",
                                    "detail": "get"},
                        member={'action':'POST'})

        self.resources['rbd_pools'] = rbd_pools.create_resource(ext_mgr)
        mapper.resource("rbd_pools", "rbd_pools",
                        controller=self.resources['rbd_pools'],
                        collection={"summary": "get",
                                    "detail": "get"},
                        member={'action':'POST'})

        self.resources['devices'] = devices.create_resource(ext_mgr)
        mapper.resource("devices", "devices",
                        controller=self.resources['devices'],
                        collection={"detail": "get",
                                    "get_available_disks":"get",
                                    "get_smart_info":"get",},
                        member={'action':'POST'})

        self.resources['licenses'] = licenses.create_resource(ext_mgr)
        mapper.resource("licenses", "licenses",
                        controller=self.resources['licenses'],
                        collection={'license_status_get': 'get',
                                    'license_status_create': 'post',
                                    'license_status_update': 'post'},
                        member={'action': 'post'})

        self.resources['vsm_settings'] = vsm_settings.create_resource(ext_mgr)
        mapper.resource("vsm_settings", "vsm_settings",
                        controller=self.resources['vsm_settings'],
                        collection={'detail': 'get',
                                    'create': 'post',
                                    'get_by_name': 'get'},
                        member={'action': 'post'})

        self.resources['performance_metrics'] = performance_metrics.create_resource(ext_mgr)
        mapper.resource("performance_metrics", "performance_metrics",
                        controller=self.resources['performance_metrics'],
                        collection={"get_list": "get",
                                    "get_metrics": "get",
                                    "get_metrics_all_types": "get",
                                    },
                        member={'action':'post'})

        self.resources['poolusages'] = poolusages.create_resource(ext_mgr)
        mapper.resource("poolusages", "poolusages",
                        controller=self.resources['poolusages'],
                        collection={'revoke_pool': "post"},
                        member={'action':'post'})

        self.resources['ec_profiles'] = ec_profiles.create_resource(ext_mgr)
        mapper.resource("ec_profiles", "ec_profiles",
                        controller=self.resources['ec_profiles'],
                        collection={
                            'detail':"get",
                            'ec_profile_create': "post",
                            'ec_profile_update': "post",
                            'ec_profiles_remove': "post",
                            },
                        member={'action': 'post'})

        self.resources['rgws'] = rgw.create_resource(ext_mgr)
        mapper.resource("rgws", "rgws",
                        controller=self.resources['rgws'],
                        collection={},
                        member={'action':'post'})