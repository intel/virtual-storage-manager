#  Copyright 2014 Intel Corporation, All Rights Reserved.
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

from vsmclient import client
from vsmclient.v1 import limits
from vsmclient.v1 import quota_classes
from vsmclient.v1 import quotas
from vsmclient.v1 import vsms
from vsmclient.v1 import clusters
from vsmclient.v1 import zones
from vsmclient.v1 import servers
from vsmclient.v1 import vsm_snapshots
from vsmclient.v1 import vsm_types
from vsmclient.v1 import osds
from vsmclient.v1 import mdses
from vsmclient.v1 import monitors
from vsmclient.v1 import storage_groups
from vsmclient.v1 import placement_groups
from vsmclient.v1 import rbd_pools 
from vsmclient.v1 import devices
from vsmclient.v1 import storage_pools
from vsmclient.v1 import appnodes
from vsmclient.v1 import licenses
from vsmclient.v1 import vsm_settings
from vsmclient.v1 import performance_metrics
from vsmclient.v1 import pool_usages
from vsmclient.v1 import ec_profiles
from vsmclient.v1 import rgws

class Client(object):
    """
    Top-level object to access the OpenStack Volume API.

    Create an instance with your creds::

        >>> client = Client(USERNAME, PASSWORD, PROJECT_ID, AUTH_URL)

    Then call methods on its managers::

        >>> client.vsms.list()
        ...

    """

    def __init__(self, username, api_key, project_id=None, auth_url='',
                 insecure=False, timeout=None, tenant_id=None,
                 proxy_tenant_id=None, proxy_token=None, region_name=None,
                 endpoint_type='publicURL', extensions=None,
                 service_type='vsm', service_name=None,
                 vsm_service_name=None, retries=None,
                 http_log_debug=False,
                 cacert=None):
        # FIXME(comstud): Rename the api_key argument above when we
        # know it's not being used as keyword argument
        password = api_key
        self.limits = limits.LimitsManager(self)

        # extensions
        self.vsms = vsms.VolumeManager(self)
        self.clusters = clusters.ClusterManager(self)
        self.zones = zones.ZoneManager(self)
        self.servers = servers.ServerManager(self)
        self.vsm_snapshots = vsm_snapshots.SnapshotManager(self)
        self.vsm_types = vsm_types.VolumeTypeManager(self)
        self.quota_classes = quota_classes.QuotaClassSetManager(self)
        self.quotas = quotas.QuotaSetManager(self)
        self.osds = osds.OsdManager(self)
        self.mdses = mdses.MdsesManager(self)
        self.monitors = monitors.MonitorsManager(self)
        self.storage_groups = storage_groups.StorageGroupsManager(self)
        self.placement_groups = placement_groups.PlacementGroupsManager(self)
        self.rbd_pools = rbd_pools.RBDPoolsManager(self)
        self.devices = devices.DeviceManager(self)
        self.storage_pools = storage_pools.StoragePoolManager(self)
        # self.mons = mons.MonitorsManager(self)
        self.appnodes = appnodes.AppNodeManager(self)
        self.licenses = licenses.LicenseManager(self)
        self.vsm_settings = vsm_settings.VsmSettingsManager(self)
        self.performance_metrics = performance_metrics.PerformanceMetricsManager(self)
        self.pool_usages = pool_usages.PoolUsageManager(self)
        self.ec_profiles = ec_profiles.ECProfilesManager(self)
        self.rgws = rgws.RgwManager(self)

        # Add in any extensions...
        if extensions:
            for extension in extensions:
                if extension.manager_class:
                    setattr(self, extension.name,
                            extension.manager_class(self))

        self.client = client.HTTPClient(
            username,
            password,
            project_id,
            auth_url,
            insecure=insecure,
            timeout=timeout,
            tenant_id=tenant_id,
            proxy_token=proxy_token,
            proxy_tenant_id=proxy_tenant_id,
            region_name=region_name,
            endpoint_type=endpoint_type,
            service_type=service_type,
            service_name=service_name,
            vsm_service_name=vsm_service_name,
            retries=retries,
            http_log_debug=http_log_debug,
            cacert=cacert)

    def authenticate(self):
        """
        Authenticate against the server.

        Normally this is called automatically when you first access the API,
        but you can call this method to force authentication right now.

        Returns on success; raises :exc:`exceptions.Unauthorized` if the
        credentials are wrong.
        """
        self.client.authenticate()
