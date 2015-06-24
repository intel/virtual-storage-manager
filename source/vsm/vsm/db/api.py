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

"""Defines interface for DB access.

The underlying driver is loaded as a :class:`LazyPluggable`.

Functions in this module are imported into the vsm.db namespace. Call these
functions from vsm.db namespace, not the vsm.db.api namespace.

All functions in this module return objects that implement a dictionary-like
interface. Currently, many of these objects are sqlalchemy objects that
implement a dictionary interface. However, a future goal is to have all of
these objects be simple dictionaries.

**Related Flags**

:db_backend:  string to lookup in the list of LazyPluggable backends.
              `sqlalchemy` is the only supported backend right now.

:sql_connection:  string specifying the sqlalchemy connection to use, like:
                  `sqlite:///var/lib/vsm/vsm.sqlite`.

:enable_new_services:  when adding a new service to the database, is it in the
                       pool of available storage (Default: True)

"""

from oslo.config import cfg

from vsm import exception
from vsm import flags
from vsm import utils

db_opts = [
    cfg.StrOpt('db_backend',
               default='sqlalchemy',
               help='The backend to use for db'),
    cfg.BoolOpt('enable_new_services',
                default=True,
                help='Services to be added to the available pool on create'),
    cfg.StrOpt('storage_name_template',
               default='storage-%s',
               help='Template string to be used to generate storage names'),
    cfg.StrOpt('snapshot_name_template',
               default='snapshot-%s',
               help='Template string to be used to generate snapshot names'),
    cfg.StrOpt('backup_name_template',
               default='backup-%s',
               help='Template string to be used to generate backup names'), ]

FLAGS = flags.FLAGS
FLAGS.register_opts(db_opts)

IMPL = utils.LazyPluggable('db_backend',
                           sqlalchemy='vsm.db.sqlalchemy.api')

class NoMoreTargets(exception.VsmException):
    """No more available targets"""
    pass

###################

def device_get_by_name(context, device_name):
    return IMPL.device_get_by_name(context, device_name)

def service_destroy(context, service_id):
    """Destroy the service or raise if it does not exist."""
    return IMPL.service_destroy(context, service_id)

def service_get(context, service_id):
    """Get a service or raise if it does not exist."""
    return IMPL.service_get(context, service_id)

def service_get_by_host_and_topic(context, host, topic):
    """Get a service by host it's on and topic it listens to."""
    return IMPL.service_get_by_host_and_topic(context, host, topic)

def service_get_all(context, disabled=None):
    """Get all services."""
    return IMPL.service_get_all(context, disabled)

def service_get_all_by_topic(context, topic):
    """Get all services for a given topic."""
    return IMPL.service_get_all_by_topic(context, topic)

def service_get_all_by_host(context, host):
    """Get all services for a given host."""
    return IMPL.service_get_all_by_host(context, host)

def service_get_all_bmc_by_host(context, host):
    """Get all compute services for a given host."""
    return IMPL.service_get_all_bmc_by_host(context, host)

def service_get_all_storage_sorted(context):
    """Get all storage services sorted by storage count.

    :returns: a list of (Service, storage_count) tuples.

    """
    return IMPL.service_get_all_storage_sorted(context)

def service_get_by_args(context, host, binary):
    """Get the state of an service by node name and binary."""
    return IMPL.service_get_by_args(context, host, binary)

def service_create(context, values):
    """Create a service from the values dictionary."""
    return IMPL.service_create(context, values)

def service_update(context, service_id, values):
    """Set the given properties on an service and update it.

    Raises NotFound if service does not exist.

    """
    return IMPL.service_update(context, service_id, values)

###################

def compute_node_get(context, compute_id):
    """Get an computeNode or raise if it does not exist."""
    return IMPL.compute_node_get(context, compute_id)

def compute_node_get_all(context):
    """Get all computeNodes."""
    return IMPL.compute_node_get_all(context)

def compute_node_create(context, values):
    """Create a computeNode from the values dictionary."""
    return IMPL.compute_node_create(context, values)

def compute_node_update(context, compute_id, values, auto_adjust=True):
    """Set the given properties on an computeNode and update it.

    Raises NotFound if computeNode does not exist.
    """
    return IMPL.compute_node_update(context, compute_id, values, auto_adjust)

def compute_node_get_by_host(context, host):
    return IMPL.compute_node_get_by_host(context, host)

def compute_node_utilization_update(context, host, free_ram_mb_delta=0,
                          free_disk_gb_delta=0, work_delta=0, vm_delta=0):
    return IMPL.compute_node_utilization_update(context, host,
                          free_ram_mb_delta, free_disk_gb_delta, work_delta,
                          vm_delta)

def compute_node_utilization_set(context, host, free_ram_mb=None,
                                 free_disk_gb=None, work=None, vms=None):
    return IMPL.compute_node_utilization_set(context, host, free_ram_mb,
                                             free_disk_gb, work, vms)

###################
# Standby Table
def standby_service_create(context, values):
    """Create a standby service info from the values dictionary."""
    return IMPL.standby_service_create(context, values)

def standby_service_update(context, host_name, values):
    """Create a stadnby service info from the values dictionary."""
    return IMPL.standby_service_update(context, host_name, values)

def standby_service_get_by_hostname(context, host_name):
    """Create a stadnby service info from the values dictionary."""
    return IMPL.standby_service_get_by_hostname(context, host_name)

def standby_service_get_all(context):
    """Create a stadnby service info from the values dictionary."""
    return IMPL.standby_service_get_all(context)

def standby_setting_get_by_id(context, id):
    """get standby setting by id"""
    return IMPL.standby_setting_get_by_id(context, id)

def standby_setting_update_by_id(context, id, data):
    return IMPL.standby_setting_update_by_id(context, id, data)
###################
def migration_update(context, id, values):
    """Update a migration instance."""
    return IMPL.migration_update(context, id, values)

def migration_create(context, values):
    """Create a migration record."""
    return IMPL.migration_create(context, values)

def migration_get(context, migration_id):
    """Finds a migration by the id."""
    return IMPL.migration_get(context, migration_id)

def migration_get_by_instance_and_status(context, instance_uuid, status):
    """Finds a migration by the instance uuid its migrating."""
    return IMPL.migration_get_by_instance_and_status(context,
                                                     instance_uuid,
                                                     status)

def migration_get_all_unconfirmed(context, confirm_window):
    """Finds all unconfirmed migrations within the confirmation window."""
    return IMPL.migration_get_all_unconfirmed(context, confirm_window)

###################

def iscsi_target_count_by_host(context, host):
    """Return count of export devices."""
    return IMPL.iscsi_target_count_by_host(context, host)

def iscsi_target_create_safe(context, values):
    """Create an iscsi_target from the values dictionary.

    The device is not returned. If the create violates the unique
    constraints because the iscsi_target and host already exist,
    no exception is raised.

    """
    return IMPL.iscsi_target_create_safe(context, values)

###############

def storage_allocate_iscsi_target(context, storage_id, host):
    """Atomically allocate a free iscsi_target from the pool."""
    return IMPL.storage_allocate_iscsi_target(context, storage_id, host)

def storage_attached(context, storage_id, instance_id, mountpoint):
    """Ensure that a storage is set as attached."""
    return IMPL.storage_attached(context, storage_id, instance_id, mountpoint)

def storage_create(context, values):
    """Create a storage from the values dictionary."""
    return IMPL.storage_create(context, values)

def storage_data_get_for_host(context, host, session=None):
    """Get (storage_count, gigabytes) for project."""
    return IMPL.storage_data_get_for_host(context,
                                         host,
                                         session)

def storage_data_get_for_project(context, project_id, session=None):
    """Get (storage_count, gigabytes) for project."""
    return IMPL.storage_data_get_for_project(context,
                                            project_id,
                                            session)

def storage_destroy(context, storage_id):
    """Destroy the storage or raise if it does not exist."""
    return IMPL.storage_destroy(context, storage_id)

def storage_detached(context, storage_id):
    """Ensure that a storage is set as detached."""
    return IMPL.storage_detached(context, storage_id)

def storage_get(context, storage_id):
    """Get a storage or raise if it does not exist."""
    return IMPL.storage_get(context, storage_id)

def storage_get_all(context, marker, limit, sort_key, sort_dir):
    """Get all storages."""
    return IMPL.storage_get_all(context, marker, limit, sort_key, sort_dir)

def storage_get_all_by_host(context, host):
    """Get all storages belonging to a host."""
    return IMPL.storage_get_all_by_host(context, host)

def storage_get_all_by_instance_uuid(context, instance_uuid):
    """Get all storages belonging to a instance."""
    return IMPL.storage_get_all_by_instance_uuid(context, instance_uuid)

def storage_get_all_by_project(context, project_id, marker, limit, sort_key,
                              sort_dir):
    """Get all storages belonging to a project."""
    return IMPL.storage_get_all_by_project(context, project_id, marker, limit,
                                          sort_key, sort_dir)

def storage_get_iscsi_target_num(context, storage_id):
    """Get the target num (tid) allocated to the storage."""
    return IMPL.storage_get_iscsi_target_num(context, storage_id)

def storage_update(context, storage_id, values):
    """Set the given properties on an storage and update it.

    Raises NotFound if storage does not exist.

    """
    return IMPL.storage_update(context, storage_id, values)

####################

def snapshot_create(context, values):
    """Create a snapshot from the values dictionary."""
    return IMPL.snapshot_create(context, values)

def snapshot_destroy(context, snapshot_id):
    """Destroy the snapshot or raise if it does not exist."""
    return IMPL.snapshot_destroy(context, snapshot_id)

def snapshot_get(context, snapshot_id):
    """Get a snapshot or raise if it does not exist."""
    return IMPL.snapshot_get(context, snapshot_id)

def snapshot_get_all(context):
    """Get all snapshots."""
    return IMPL.snapshot_get_all(context)

def snapshot_get_all_by_project(context, project_id):
    """Get all snapshots belonging to a project."""
    return IMPL.snapshot_get_all_by_project(context, project_id)

def snapshot_get_all_for_storage(context, storage_id):
    """Get all snapshots for a storage."""
    return IMPL.snapshot_get_all_for_storage(context, storage_id)

def snapshot_update(context, snapshot_id, values):
    """Set the given properties on an snapshot and update it.

    Raises NotFound if snapshot does not exist.

    """
    return IMPL.snapshot_update(context, snapshot_id, values)

def snapshot_data_get_for_project(context, project_id, session=None):
    """Get count and gigabytes used for snapshots for specified project."""
    return IMPL.snapshot_data_get_for_project(context,
                                              project_id,
                                              session)

####################

def snapshot_metadata_get(context, snapshot_id):
    """Get all metadata for a snapshot."""
    return IMPL.snapshot_metadata_get(context, snapshot_id)

def snapshot_metadata_delete(context, snapshot_id, key):
    """Delete the given metadata item."""
    IMPL.snapshot_metadata_delete(context, snapshot_id, key)

def snapshot_metadata_update(context, snapshot_id, metadata, delete):
    """Update metadata if it exists, otherwise create it."""
    IMPL.snapshot_metadata_update(context, snapshot_id, metadata, delete)

####################

def storage_metadata_get(context, storage_id):
    """Get all metadata for a storage."""
    return IMPL.storage_metadata_get(context, storage_id)

def storage_metadata_delete(context, storage_id, key):
    """Delete the given metadata item."""
    IMPL.storage_metadata_delete(context, storage_id, key)

def storage_metadata_update(context, storage_id, metadata, delete):
    """Update metadata if it exists, otherwise create it."""
    IMPL.storage_metadata_update(context, storage_id, metadata, delete)

##################

def storage_type_create(context, values):
    """Create a new storage type."""
    return IMPL.storage_type_create(context, values)

def storage_type_get_all(context, inactive=False):
    """Get all storage types."""
    return IMPL.storage_type_get_all(context, inactive)

def storage_type_get(context, id):
    """Get storage type by id."""
    return IMPL.storage_type_get(context, id)

def storage_type_get_by_name(context, name):
    """Get storage type by name."""
    return IMPL.storage_type_get_by_name(context, name)

def storage_type_destroy(context, id):
    """Delete a storage type."""
    return IMPL.storage_type_destroy(context, id)

def storage_get_active_by_window(context, begin, end=None, project_id=None):
    """Get all the storages inside the window.

    Specifying a project_id will filter for a certain project."""
    return IMPL.storage_get_active_by_window(context, begin, end, project_id)

####################

def storage_type_extra_specs_get(context, storage_type_id):
    """Get all extra specs for a storage type."""
    return IMPL.storage_type_extra_specs_get(context, storage_type_id)

def storage_type_extra_specs_delete(context, storage_type_id, key):
    """Delete the given extra specs item."""
    IMPL.storage_type_extra_specs_delete(context, storage_type_id, key)

def storage_type_extra_specs_update_or_create(context,
                                             storage_type_id,
                                             extra_specs):
    """Create or update storage type extra specs. This adds or modifies the
    key/value pairs specified in the extra specs dict argument"""
    IMPL.storage_type_extra_specs_update_or_create(context,
                                                  storage_type_id,
                                                  extra_specs)

###################

def storage_glance_metadata_create(context, storage_id, key, value):
    """Update the Glance metadata for the specified storage."""
    return IMPL.storage_glance_metadata_create(context,
                                              storage_id,
                                              key,
                                              value)

def storage_glance_metadata_get(context, storage_id):
    """Return the glance metadata for a storage."""
    return IMPL.storage_glance_metadata_get(context, storage_id)

def storage_snapshot_glance_metadata_get(context, snapshot_id):
    """Return the Glance metadata for the specified snapshot."""
    return IMPL.storage_snapshot_glance_metadata_get(context, snapshot_id)

def storage_glance_metadata_copy_to_snapshot(context, snapshot_id, storage_id):
    """
    Update the Glance metadata for a snapshot by copying all of the key:value
    pairs from the originating storage. This is so that a storage created from
    the snapshot will retain the original metadata.
    """
    return IMPL.storage_glance_metadata_copy_to_snapshot(context, snapshot_id,
                                                        storage_id)

def storage_glance_metadata_copy_to_storage(context, storage_id, snapshot_id):
    """
    Update the Glance metadata from a storage (created from a snapshot) by
    copying all of the key:value pairs from the originating snapshot. This is
    so that the Glance metadata from the original storage is retained.
    """
    return IMPL.storage_glance_metadata_copy_to_storage(context, storage_id,
                                                      snapshot_id)

def storage_glance_metadata_delete_by_storage(context, storage_id):
    """Delete the glance metadata for a storage."""
    return IMPL.storage_glance_metadata_delete_by_storage(context, storage_id)

def storage_glance_metadata_delete_by_snapshot(context, snapshot_id):
    """Delete the glance metadata for a snapshot."""
    return IMPL.storage_glance_metadata_delete_by_snapshot(context, snapshot_id)

def storage_glance_metadata_copy_from_storage_to_storage(context,
                                                      src_storage_id,
                                                      storage_id):
    """
    Update the Glance metadata for a storage by copying all of the key:value
    pairs from the originating storage. This is so that a storage created from
    the storage (clone) will retain the original metadata.
    """
    return IMPL.storage_glance_metadata_copy_from_storage_to_storage(
        context,
        src_storage_id,
        storage_id)

###################

def sm_backend_conf_create(context, values):
    """Create a new SM Backend Config entry."""
    return IMPL.sm_backend_conf_create(context, values)

def sm_backend_conf_update(context, sm_backend_conf_id, values):
    """Update a SM Backend Config entry."""
    return IMPL.sm_backend_conf_update(context, sm_backend_conf_id, values)

def sm_backend_conf_delete(context, sm_backend_conf_id):
    """Delete a SM Backend Config."""
    return IMPL.sm_backend_conf_delete(context, sm_backend_conf_id)

def sm_backend_conf_get(context, sm_backend_conf_id):
    """Get a specific SM Backend Config."""
    return IMPL.sm_backend_conf_get(context, sm_backend_conf_id)

def sm_backend_conf_get_by_sr(context, sr_uuid):
    """Get a specific SM Backend Config."""
    return IMPL.sm_backend_conf_get_by_sr(context, sr_uuid)

def sm_backend_conf_get_all(context):
    """Get all SM Backend Configs."""
    return IMPL.sm_backend_conf_get_all(context)

####################

def sm_flavor_create(context, values):
    """Create a new SM Flavor entry."""
    return IMPL.sm_flavor_create(context, values)

def sm_flavor_update(context, sm_flavor_id, values):
    """Update a SM Flavor entry."""
    return IMPL.sm_flavor_update(context, values)

def sm_flavor_delete(context, sm_flavor_id):
    """Delete a SM Flavor."""
    return IMPL.sm_flavor_delete(context, sm_flavor_id)

def sm_flavor_get(context, sm_flavor):
    """Get a specific SM Flavor."""
    return IMPL.sm_flavor_get(context, sm_flavor)

def sm_flavor_get_all(context):
    """Get all SM Flavors."""
    return IMPL.sm_flavor_get_all(context)

####################

def sm_storage_create(context, values):
    """Create a new child Zone entry."""
    return IMPL.sm_storage_create(context, values)

def sm_storage_update(context, storage_id, values):
    """Update a child Zone entry."""
    return IMPL.sm_storage_update(context, values)

def sm_storage_delete(context, storage_id):
    """Delete a child Zone."""
    return IMPL.sm_storage_delete(context, storage_id)

def sm_storage_get(context, storage_id):
    """Get a specific child Zone."""
    return IMPL.sm_storage_get(context, storage_id)

def sm_storage_get_all(context):
    """Get all child Zones."""
    return IMPL.sm_storage_get_all(context)

###################

def quota_create(context, project_id, resource, limit):
    """Create a quota for the given project and resource."""
    return IMPL.quota_create(context, project_id, resource, limit)

def quota_get(context, project_id, resource):
    """Retrieve a quota or raise if it does not exist."""
    return IMPL.quota_get(context, project_id, resource)

def quota_get_all_by_project(context, project_id):
    """Retrieve all quotas associated with a given project."""
    return IMPL.quota_get_all_by_project(context, project_id)

def quota_update(context, project_id, resource, limit):
    """Update a quota or raise if it does not exist."""
    return IMPL.quota_update(context, project_id, resource, limit)

def quota_destroy(context, project_id, resource):
    """Destroy the quota or raise if it does not exist."""
    return IMPL.quota_destroy(context, project_id, resource)

###################

def quota_class_create(context, class_name, resource, limit):
    """Create a quota class for the given name and resource."""
    return IMPL.quota_class_create(context, class_name, resource, limit)

def quota_class_get(context, class_name, resource):
    """Retrieve a quota class or raise if it does not exist."""
    return IMPL.quota_class_get(context, class_name, resource)

def quota_class_get_all_by_name(context, class_name):
    """Retrieve all quotas associated with a given quota class."""
    return IMPL.quota_class_get_all_by_name(context, class_name)

def quota_class_update(context, class_name, resource, limit):
    """Update a quota class or raise if it does not exist."""
    return IMPL.quota_class_update(context, class_name, resource, limit)

def quota_class_destroy(context, class_name, resource):
    """Destroy the quota class or raise if it does not exist."""
    return IMPL.quota_class_destroy(context, class_name, resource)

def quota_class_destroy_all_by_name(context, class_name):
    """Destroy all quotas associated with a given quota class."""
    return IMPL.quota_class_destroy_all_by_name(context, class_name)

###################

def quota_usage_create(context, project_id, resource, in_use, reserved,
                       until_refresh):
    """Create a quota usage for the given project and resource."""
    return IMPL.quota_usage_create(context, project_id, resource,
                                   in_use, reserved, until_refresh)

def quota_usage_get(context, project_id, resource):
    """Retrieve a quota usage or raise if it does not exist."""
    return IMPL.quota_usage_get(context, project_id, resource)

def quota_usage_get_all_by_project(context, project_id):
    """Retrieve all usage associated with a given resource."""
    return IMPL.quota_usage_get_all_by_project(context, project_id)

###################

def reservation_create(context, uuid, usage, project_id, resource, delta,
                       expire):
    """Create a reservation for the given project and resource."""
    return IMPL.reservation_create(context, uuid, usage, project_id,
                                   resource, delta, expire)

def reservation_get(context, uuid):
    """Retrieve a reservation or raise if it does not exist."""
    return IMPL.reservation_get(context, uuid)

def reservation_get_all_by_project(context, project_id):
    """Retrieve all reservations associated with a given project."""
    return IMPL.reservation_get_all_by_project(context, project_id)

def reservation_destroy(context, uuid):
    """Destroy the reservation or raise if it does not exist."""
    return IMPL.reservation_destroy(context, uuid)

###################

def quota_reserve(context, resources, quotas, deltas, expire,
                  until_refresh, max_age, project_id=None):
    """Check quotas and create appropriate reservations."""
    return IMPL.quota_reserve(context, resources, quotas, deltas, expire,
                              until_refresh, max_age, project_id=project_id)

def reservation_commit(context, reservations, project_id=None):
    """Commit quota reservations."""
    return IMPL.reservation_commit(context, reservations,
                                   project_id=project_id)

def reservation_rollback(context, reservations, project_id=None):
    """Roll back quota reservations."""
    return IMPL.reservation_rollback(context, reservations,
                                     project_id=project_id)

def quota_destroy_all_by_project(context, project_id):
    """Destroy all quotas associated with a given project."""
    return IMPL.quota_destroy_all_by_project(context, project_id)

def reservation_expire(context):
    """Roll back any expired reservations."""
    return IMPL.reservation_expire(context)

###################

def backup_get(context, backup_id):
    """Get a backup or raise if it does not exist."""
    return IMPL.backup_get(context, backup_id)

def backup_get_all(context):
    """Get all backups."""
    return IMPL.backup_get_all(context)

def backup_get_all_by_host(context, host):
    """Get all backups belonging to a host."""
    return IMPL.backup_get_all_by_host(context, host)

def backup_create(context, values):
    """Create a backup from the values dictionary."""
    return IMPL.backup_create(context, values)

def backup_get_all_by_project(context, project_id):
    """Get all backups belonging to a project."""
    return IMPL.backup_get_all_by_project(context, project_id)

def backup_update(context, backup_id, values):
    """
    Set the given properties on a backup and update it.

    Raises NotFound if backup does not exist.
    """
    return IMPL.backup_update(context, backup_id, values)

def backup_destroy(context, backup_id):
    """Destroy the backup or raise if it does not exist."""
    return IMPL.backup_destroy(context, backup_id)

#bellow is about osd state table operating
def osd_get(context, osd_id):
    """"get a entry according to specify osd_id"""
    return IMPL.osd_get(context, osd_id)

def osd_get_all(context, session=None):
    """get information about all osds"""
    return IMPL.osd_get_all(context, session)

def osd_get_all_down(context, session=None):
    """get information about all down osds"""
    return IMPL.osd_get_all_down(context, session)

def osd_get_all_up(context, session=None):
    """get information about all up osds"""
    return IMPL.osd_get_all_up(context, session)

def osd_get_by_service_id(context, service_id, session=None):
    """get osds by service id"""
    return IMPL.osd_get_by_service_id(context, service_id, session)

def osd_get_by_cluster_id(context, cluster_id, session=None):
    """get osds by cluster id"""
    return IMPL.osd_get_by_cluster_id(context, cluster_id, session)

def osd_destroy(context, osd_id):
    """Destory a osd."""
    return IMPL.osd_destroy(context, osd_id)

def osd_create(context, values):
    """create a osd from the values dictionary"""
    return IMPL.osd_create(context, values)

def osd_update(context, osd_id, values):
    """update a osd from the values dictionary"""
    return IMPL.osd_update(context, osd_id, values)

def osd_delete(context, osd_id):
    """delete a osd according to specify osd id"""
    return IMPL.osd_delete(context, osd_id)

#bellow is about the operation on crushmap
#@DEBUG
def crushmap_get(context, crushmap_id):
    """get a crushmap according to specify osd_id"""
    return IMPL.crushmap_get(context, crushmap_id)

def crushmap_get_all(context):
    """get all crushmaps"""
    return IMPL.crushmap_get_all(context)

def crushmap_create(context, values):
    """create a crushmap from the values dictionary"""
    return IMPL.crushmap_create(context, values)

def crushmap_update(context, crushmap_id, values):
    """update a crushmap from the values dictionary"""
    return IMPL.crushmap_update(context, crushmap_id, values)

def crushmap_delete(context, crushmap_id):
    """delete a osd according to specify crushmap id"""
    return IMPL.crushmap_delete(context, crushmap_id)

#bellow is about the operation on devices
def device_get(context, device_id):
    """get a device according to specify device_id"""
    return IMPL.device_get(context, device_id)

def device_get_all(context):
    """get all devices"""
    return IMPL.device_get_all(context)

def device_get_all_by_interface_type(context, interface_type):
    """get all devices by interface type"""
    return IMPL.device_get_all_by_interface_type(context, interface_type)

def device_get_all_by_device_type(context, device_type):
    """get all devices by device type"""
    return IMPL.device_get_all_by_device_type(context, device_type)

def device_get_all_by_service_id(context, service_id):
    """get all devices by service id"""
    return IMPL.device_get_all_by_service_id(context, service_id)

def device_get_all_by_state(context, state):
    """get all devices by state"""
    return IMPL.device_get_all_by_state(context, state)

def device_create(context, values):
    """create a device from the values dictionary"""
    return IMPL.device_create(context, values)

def device_update(context, device_id, values):
    """update a device from the values dictionary"""
    return IMPL.device_update(context, device_id, values)

def device_delete(context, device_id):
    """delete a device according to specify device id"""
    return IMPL.device_delete(context, device_id)

#bellow is about the operation on VSM user capacity management
def vsm_capacity_manage_get(context, vsm_capacity_manage_id):
    """get a user according to specify vsm_capacity_manage_id"""
    return IMPL.vsm_capacity_manage_get(context, vsm_capacity_manage_id)

def vsm_capacity_manage_get_all(context):
    """get all VSM users"""
    return IMPL.vsm_capacity_manage_get_all(context)

def vsm_capacity_manage_create(context, values):
    """create a VSM user from the values dictionary"""
    return IMPL.vsm_capacity_manage_create(context, values)

def vsm_capacity_manage_update(context, vsm_capacity_manage_id, values):
    """update a VSM user from the values dictionary"""
    return IMPL.vsm_capacity_manage_update(context, vsm_capacity_manage_id, values)

def vsm_capacity_manage_delete(context, vsm_capacity_manage_id):
    """delete a VSM user according to specify vsm_capacity_manage_id"""
    return IMPL.vsm_capacity_manage_delete(context, vsm_capacity_manage_id)

#bellow is about the operation on recipes
def recipe_get(context, recipe_id):
    """Get an recipe or raise if it does not exist."""
    return IMPL.recipe_get(context, recipe_id)

def recipe_get_all(context):
    """Get all recipes."""
    return IMPL.recipe_get_all(context)

def recipe_create(context, values):
    """Create a recipe from the values dictionary."""
    return IMPL.recipe_create(context, values)

def recipe_update(context, recipe_id, values):
    """Set the given properties on an recipe and update it.

    Raises NotFound if recipe does not exist.
    """
    return IMPL.recipe_update(context, recipe_id, values)

def recipe_delete(context, recipe_id):
    """Delete an recipe by recipe_id"""
    return IMPL.recipe_delete(context, recipe_id)

##storage pool
def pool_get_all(context):
    """get all pools"""
    return IMPL.pool_get_all(context)

def pool_get(context, pool_id):
    return IMPL.pool_get(context, pool_id)

def pool_get_by_name(context, pool_name, cluster_id):
    return IMPL.pool_get_by_name(context, pool_name, cluster_id)

def pool_create(context, values):
    """create a pool from the values dictionary"""
    return IMPL.pool_create(context, values)

def pool_update(context, pool_id, values):
    """update a pool with pool_id and values"""
    return IMPL.pool_update(context, pool_id, values)

def pool_update_by_name(context, pool_name, cluster_id, values):
    """update a pool with pool_name, cluster_id and values"""
    return IMPL.pool_update_by_name(context, pool_name, cluster_id, values)

#this pool_id is not the db id
def pool_update_by_pool_id(context, pool_id, values):
    return IMPL.pool_update_by_pool_id(context, pool_id, values)

def pool_get_by_ruleset(context, ruleset):
    return IMPL.pool_get_by_ruleset(context, ruleset)

def pool_destroy(context, pool_name):
    return IMPL.pool_destroy(context, pool_name)

#manange cluster
def cluster_get_all(context):
    """get all clusters"""
    return IMPL.cluster_get_all(context)

def cluster_create(context, values):
    """create a cluster from the values dictionary"""
    return IMPL.cluster_create(context, values)

def cluster_update(context, cluster_id, values):
    """update a cluster with cluster_id and values"""
    return IMPL.cluster_update(context, cluster_id, values)

def cluster_get(context, cluster_id):
    """Get an cluster with cluster_id"""
    return IMPL.cluster_get(context, cluster_id)

def cluster_increase_deleted_times(context, cluster_id):
    return IMPL.cluster_increase_deleted_times(context, cluster_id)

def cluster_update_ceph_conf(context, cluster_id, ceph_conf):
    return IMPL.cluster_update_ceph_conf(context, cluster_id, ceph_conf)

def cluster_get_ceph_conf(context, cluster_id):
    return IMPL.cluster_get_ceph_conf(context, cluster_id)

def cluster_get_deleted_times(context, cluster_id):
    return IMPL.cluster_get_deleted_times(context, cluster_id)

def cluster_info_dict_get_by_id(context, cluster_id):
    return IMPL.cluster_info_dict_get_by_id(context, cluster_id)

#manange storage_group
def storage_group_get_all(context):
    """get all storage_groups"""
    return IMPL.storage_group_get_all(context)

def storage_group_get_by_rule_id(context, rule_id):
    return IMPL.storage_group_get_by_rule_id(context, rule_id)

def storage_group_get_by_storage_class(context, storage_class):
    return IMPL.storage_group_get_by_storage_class(context, storage_class)

def storage_group_update_by_name(context, name, values):
    return IMPL.storage_group_update_by_name(context, name, values)

def create_storage_group(context, values):
    if values is None:
        return False

    res = storage_group_get_all(context)
    name_list = []
    for item in res:
        name_list.append(item['name'])

    if values['name'] not in name_list:
        storage_group_create(context, values)
    else:
        return False

    return True

def storage_group_create(context, values):
    """create a storage_group from the values dictionary"""
    return IMPL.storage_group_create(context, values)

def storage_group_update(context, group_id, values):
    """update a storage_group with group_id and values"""
    return IMPL.storage_group_update(context, group_id, values)

def storage_group_get(context, group_id):
    """Get an storage_group with group_id"""
    return IMPL.storage_group_get(context, group_id)

#manange zone
def zone_get_all(context):
    """get all zones"""
    return IMPL.zone_get_all(context)

def create_zone(context, values=None):
    if values is None:
        return False

    res = zone_get_all(context)
    zone_list = []
    for item in res:
        zone_list.append(item['name'])

    if values['name'] not in zone_list:
        zone_create(context, values)
    else:
        return True

    return True

def zone_create(context, values):
    """create a zone from the values dictionary"""
    return IMPL.zone_create(context, values)

def zone_update(context, zone_id, values):
    """update a zone with zone_id and values"""
    return IMPL.zone_update(context, zone_id, values)

def zone_get(context, zone_id):
    """Get an zone with zone_id"""
    return IMPL.zone_get(context, zone_id)

#manage agent host info
def compute_node_update_no_context(service_id, values):
    """"""
    return IMPL.compute_node_update_no_context(service_id, values)

def service_get_by_host_and_topic_no_context(host, topic):
    """Get a service or raise if it does not exist."""
    return IMPL.service_get_by_host_and_topic_no_context(host, topic)

#server
def server_get_all(context):
    """"""
    return IMPL.server_get_all(context)
                                                      

def init_node_get_all(context):
    return IMPL.init_node_get_all(context)

def init_node_get(context, id):
    return IMPL.init_node_get(context, id)

def init_node_get_by_host(context, host, session=None):
    """Get init node ref by host name."""
    return IMPL.init_node_get_by_host(context, host, session)

def init_node_get_by_cluster_id(context, cluster_id, session=None):
    """Get init node ref by cluster id."""
    return IMPL.init_node_get_by_cluster_id(context, cluster_id, session)

def init_node_get_cluster_nodes(context, init_node_id, session=None):
    """Get active nodes in the same cluster."""
    return IMPL.init_node_get_cluster_nodes(context, init_node_id, session)
def init_node_get_by_device_id(context, device_id, session=None):
    """Get active nodes in the same cluster."""
    return IMPL.init_node_get_by_device_id(context, device_id, session)
#cluster
def cluster_get_by_name(context, values):
    return IMPL.cluster_get_by_name(context, values)

#init_node
def init_node_create(context, values):
    return IMPL.init_node_create(context, values)

def init_node_get_by_primary_public_ip(context, primary_public_ip):
    return IMPL.init_node_get_by_primary_public_ip(context, primary_public_ip)

def init_node_get_by_secondary_public_ip(context, secondary_public_ip):
    return IMPL.init_node_get_by_secondary_public_ip(context, \
                                                     secondary_public_ip)

def init_node_get_by_cluster_ip(context, cluster_ip):
    return IMPL.init_node_get_by_cluster_ip(context, cluster_ip)

def init_node_update(context, init_node_id, values):
    return IMPL.init_node_update(context, init_node_id, values)

def init_node_update_status_by_id(context, init_node_id, status):
    return IMPL.init_node_update_status_by_id(context, init_node_id, status)

def init_node_get_by_id_and_type(context, id, type):
    return IMPL.init_node_get_by_id_and_type(context, id, type)

def init_node_get_by_id(context, id):
    return IMPL.init_node_get_by_id(context, id)

def init_node_get_by_hostname(context, hostname, session=None):
    return IMPL.init_node_get_by_hostname(context, hostname, session)

def init_node_get_by_service_id(context, service_id, session=None):
    return IMPL.init_node_get_by_service_id(context, service_id, session)

def init_node_count_by_status(context, status):
    return IMPL.init_node_count_by_status(context, status)

#osd_state
def osd_state_create(context, values):
    return IMPL.osd_state_create(context, values)

def osd_state_get(context, osd_id):
    return IMPL.osd_state_get(context, osd_id)

def osd_state_get_all(context, limit=None, marker=None, sort_keys=None, sort_dir=None):
    return IMPL.osd_state_get_all(context, limit, marker, sort_keys, sort_dir)

def osd_state_get_by_name(context, osd):
    return IMPL.osd_state_get_by_name(context, osd)

def osd_state_update(context, id, values):
    return IMPL.osd_state_update(context, id, values)

def osd_state_update_or_create(context, values):
    return IMPL.osd_state_update_or_create(context, values)

def osd_state_count_by_init_node_id(context, init_node_id):
    return IMPL.osd_state_count_by_init_node_id(context, init_node_id)

def osd_state_get_by_service_id_and_storage_group_id(context, service_id,\
                                                     storage_group_id):
    return IMPL.osd_state_get_by_service_id_and_storage_group_id(context,\
                                               service_id, storage_group_id)

def osd_state_get_by_device_id_and_service_id_and_cluster_id(\
        context, device_id, service_id, cluster_id):
    return IMPL.osd_state_get_by_device_id_and_service_id_and_cluster_id(\
        context, device_id, service_id, cluster_id)

def get_zone_hostname_storagegroup_by_osd_id(context, osd_id):
    return IMPL.get_zone_hostname_storagegroup_by_osd_id(context, osd_id)

def osd_state_get_by_service_id(context, service_id):
    return IMPL.osd_state_get_by_service_id(context, service_id)

def osd_state_get_by_osd_name_and_service_id_and_cluster_id(\
        context, osd_name, service_id, cluster_id):
    return IMPL.osd_state_get_by_osd_name_and_service_id_and_cluster_id(\
        context, osd_name, service_id, cluster_id)

#storage_group
def storage_group_get_all(context):
    return IMPL.storage_group_get_all(context)

def osd_state_count_by_storage_group_id(context, storage_group_id):
    return IMPL.osd_state_count_by_storage_group_id(context, storage_group_id)

def osd_state_count_service_id_by_storage_group_id(context, storage_group_id):
    return IMPL.osd_state_count_service_id_by_storage_group_id(context, \
                storage_group_id)

#zone 
def zone_get_all(context):
    return IMPL.zone_get_all(context)

def zone_get_by_id(context, id):
    return IMPL.zone_get_by_id(context,id)

def zone_get_by_name(context, zone):
    return IMPL.zone_get_by_name(context, zone)

#device

def device_get_all(context):
    return IMPL.device_get_all(context)

def device_get_count(context):
    return IMPL.device_get_count(context)

def device_get_by_service_id(context, service_id):
    return IMPL.device_get_by_service_id(context, service_id)

def device_get_distinct_storage_class_by_service_id(context, service_id):
    return IMPL.device_get_distinct_storage_class_by_service_id(context,\
            service_id)

def device_update_or_create(context, values):
    return IMPL.device_update_or_create(context, values)

def device_get_by_name_and_journal_and_service_id(context, name, \
                                                journal, service_id):
    return IMPL.device_get_by_name_and_journal_and_service_id(context, \
                                            name, journal, service_id)

#region vsmapp db APIs
def appnodes_get_by_id(context, id):
    return IMPL.appnodes_get_by_id(context, id)

def appnodes_get_all(context):
    return IMPL.appnodes_get_all(context)

def appnodes_create(context, values, allow_duplicate=False):
    return IMPL.appnodes_create(context, values, allow_duplicate)

def appnodes_update(context, appnode_id, values):
    return IMPL.appnodes_update(context, appnode_id, values)

def appnodes_destroy(context, appnode_id=None):
    return IMPL.appnodes_destroy(context, appnode_id)

def vsmapps_get_by_user(context):
    return IMPL.vsmapps_get_by_user(context)

def vsmapps_get_by_id(context, vsmapp_id):
    return IMPL.vsmapps_get_by_id(context, vsmapp_id)
#endregion

#region storage pool usage db APIs
def storage_pool_usage_create(context, pools):
    return IMPL.sp_usage_create(context, pools)

def storage_pool_usage_update(context, usage_id, values):
    return IMPL.sp_usage_update(context, usage_id, values)

def get_storage_pool_usage(context):
    return IMPL.get_sp_usage(context)

def get_sp_usage_by_poolid_vsmappid(context, pool_id, vsmapp_id):
    return IMPL.get_sp_usage_by_poolid_vsmappid(context, pool_id, vsmapp_id)

def destroy_storage_pool_usage(context, id):
    return IMPL.sp_usage_destroy(context, id)
#endregion

#region summary api
def summary_create(context, values):
    return IMPL.summary_create(context, values)

def summary_update(context, cluster_id, stype, values):
    return IMPL.summary_update(context, cluster_id, stype, values)

def summary_get_by_cluster_id_and_type(context, cluster_id, stype):
    return IMPL.summary_get_by_cluster_id_and_type(context, cluster_id, stype)

def summary_get_by_type_first(context, stype):
    return IMPL.summary_get_by_type_first(context, stype)
#endregion

#region monitor api

def monitor_get_all(context):
    return IMPL.monitor_get_all(context)

def monitor_get(context, id):
    return IMPL.monitor_get(context, id)

def monitor_update(context, mon_name, values):
    return IMPL.monitor_update(context, mon_name, values)

def monitor_destroy(context, mon_name):
    IMPL.monitor_destroy(context, mon_name)

#endregion

#pg api
def pg_create(context, values):
    return IMPL.pg_create(context, values)

def pg_get_all(context, limit=None, marker=None, sort_keys=None,
               sort_dir=None):
    return IMPL.pg_get_all(context, limit=limit, marker=marker,
                           sort_keys=sort_keys, sort_dir=sort_dir)

def pg_get_by_pgid(context, pgid):
    return IMPL.pg_get_by_pgid(context, pgid)

def pg_update(context, pg_id, values):
    return IMPL.pg_update(context, pg_id, values)

def pg_update_or_create(context, values):
    return IMPL.pg_update_or_create(context, values)

#rbd
def rbd_create(context, values):
    return IMPL.rbd_create(context, values)

def rbd_get_all(context, limit=None, marker=None, sort_keys=None, sort_dir=None):
    return IMPL.rbd_get_all(context, limit=limit, marker=marker, sort_keys=sort_keys,
							sort_dir=sort_dir)

def rbd_get_by_pool_and_image(context, pool, image):
    return IMPL.rbd_get_by_pool_and_image(context, pool, image)

def rbd_update(context, rbd_id, values):
    return IMPL.rbd_update(context, rbd_id, values)

def rbd_update_or_create(context, values):
    return IMPL.rbd_update_or_create(context, values)

#region license status ops
def license_status_create(context, values):
    return IMPL.license_status_create(context, values)

def license_status_get(context):
    return IMPL.license_status_get(context)

def license_status_update(context, value):
    return IMPL.license_status_update(context, value)

#endregion

#mds
def mds_create(context, values):
    return IMPL.mds_create(context, values)

def mds_get_all(context):
    return IMPL.mds_get_all(context)

def mds_get_by_gid(context, gid):
    return IMPL.mds_get_by_gid(context, gid)

def mds_update(context, mds_id, values):
    return IMPL.mds_update(context, mds_id, values)

def mds_update_or_create(context, values):
    return IMPL.mds_update_or_create(context, values)

#region vsm settings db api
def vsm_settings_update_or_create(context, values):
    return IMPL.vsm_settings_update_or_create(context, values)

def vsm_settings_get_all(context):
    return IMPL.vsm_settings_get_all(context)

def vsm_settings_get_by_name(context, name):
    return IMPL.vsm_settings_get_by_name(context, name)
#endregion

#long_call
def long_call_create(context, values):
    return IMPL.long_call_create(context, values)

def long_call_get_by_uuid(context, uuid):
    return IMPL.long_call_get_by_uuid(context, uuid)

def long_call_update(context, long_call_uuid, values):
    return IMPL.long_call_update(context, long_call_uuid, values)

def long_call_delete(context, long_call_uuid):
    return IMPL.long_call_delete(context, long_call_uuid)
#end

#region ec profile db api
def ec_profile_update_or_create(context, values):
    return IMPL.ec_profile_update_or_create(context, values)

def ec_profile_get_all(context):
    return IMPL.ec_profile_get_all(context)

def ec_profile_get(context, ec_profile_id):
    return IMPL.ec_profile_get(context, ec_profile_id)

def ec_profile_get_by_name(context, name):
    return IMPL.ec_profile_get_by_name(context, name)

def get_performance_metrics(context, search_opts):
    return IMPL.performance_metrics_query(context, search_opts=search_opts)

def get_sum_performance_metrics(context, search_opts):
    return IMPL.sum_performance_metrics(context, search_opts=search_opts)

def get_lantency(context, search_opts):
    return IMPL.lantency_performance_metrics(context, search_opts=search_opts)
#endregion
