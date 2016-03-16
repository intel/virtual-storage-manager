# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack LLC.
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

from __future__ import print_function

import sys
import time

from vsmclient import exceptions
from vsmclient.openstack.common import strutils
from vsmclient import utils


def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True):
    """Blocks while an action occurs. Periodically shows progress."""
    def print_progress(progress):
        if show_progress:
            msg = ('\rInstance %(action)s... %(progress)s%% complete'
                   % dict(action=action, progress=progress))
        else:
            msg = '\rInstance %(action)s...' % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    print()
    while True:
        obj = poll_fn(obj_id)
        status = obj.status.lower()
        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            print_progress(100)
            print("\nFinished")
            break
        elif status == "error":
            print("\nError %(action)s instance" % {'action': action})
            break
        else:
            print_progress(progress)
            time.sleep(poll_period)


def _find_cluster(cs, cluster):
    """Get a cluster by name or ID."""
    return utils.find_cluster(cs, cluster)

def _find_mds(cs, mds):
    """Get a mds by name or ID."""
    return utils.find_mds(cs, mds)

def _find_mon(cs, mon):
    """Get a mon by name or ID."""
    return utils.find_mon(cs, mon)

def _find_osd(cs, osd):
    """Get an osd by name or ID."""
    return utils.find_osd(cs, osd)

def _find_pg(cs, pg):
    """Get a pg by name or ID."""
    return utils.find_pg(cs, pg)

def _find_rbd(cs, rbd):
    """Get a rbd by name or ID."""
    return utils.find_rbd(cs, rbd)

def _find_server(cs, server):
    """Get a server by name or ID."""
    return utils.find_server(cs, server)

def _find_appnode(cs, appnode):
    """Get an appnode by name or ID."""
    return utils.find_appnode(cs, appnode)

def _find_storage_group(cs, storage_group):
    """Get a storage group by name or ID."""
    return utils.find_storage_group(cs, storage_group)

def _find_storage_pool(cs, storage_pool):
    """Get a storage pool by name or ID."""
    return utils.find_storage_pool(cs, storage_pool)

def _find_setting(cs, setting):
    """Get a setting by name or ID."""
    return utils.find_setting(cs, setting)


def _print_cluster(cluster):
    if isinstance(cluster, dict):
        utils.print_dict(cluster)
    else:
        utils.print_dict(cluster._info)

def _print_device(device):
    if isinstance(device, dict):
        utils.print_dict(device)
    else:
        utils.print_dict(device._info)

def _print_mds(mds):
    if isinstance(mds, dict):
        utils.print_dict(mds)
    else:
        utils.print_dict(mds._info)

def _print_mon(mon):
    if isinstance(mon, dict):
        utils.print_dict(mon)
    else:
        utils.print_dict(mon._info)

def _print_osd(osd):
    if isinstance(osd, dict):
        utils.print_dict(osd)
    else:
        utils.print_dict(osd._info)

def _print_pg(pg):
    if isinstance(pg, dict):
        utils.print_dict(pg)
    else:
        utils.print_dict(pg._info)

def _print_rbd(rbd):
    if isinstance(rbd, dict):
        utils.print_dict(rbd)
    else:
        utils.print_dict(rbd._info)

def _print_server(server):
    if isinstance(server, dict):
        utils.print_dict(server)
    else:
        utils.print_dict(server._info)

def _print_storage_group(storage_group):
    if isinstance(storage_group, dict):
        utils.print_dict(storage_group)
    else:
        utils.print_dict(storage_group._info)

def _print_storage_pool(storage_pool):
    if isinstance(storage_pool, dict):
        utils.print_dict(storage_pool)
    else:
        utils.print_dict(storage_pool._info)

def _print_setting(setting):
    if isinstance(setting, dict):
        utils.print_dict(setting)
    else:
        utils.print_dict(setting._info)


def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])

def _translate_storage_pool_keys(collection):
    convert = [
        ('createdDate', 'created_at'),
        ('clusterId', 'cluster_id'),
        ('createdBy', 'created_by'),
        ('crashRelayInterval', 'crash_relay_interval'),
        ('pgpNum', 'pgp_num'),
        ('crushRuleset', 'crush_ruleset'),
        ('recipeId', 'recipe_id'),
        ('minSize', 'min_size'),
        ('storageGroup', 'storage_group'),
        ('poolId', 'pool_id_duplicated'),
        ('pgNum', 'pg_num')
    ]
    _translate_keys(collection, convert)

def _extract_metadata(args):
    metadata = {}
    for metadatum in args.metadata:
        # unset doesn't require a val, so we have the if/else
        if '=' in metadatum:
            (key, value) = metadatum.split('=', 1)
        else:
            key = metadatum
            value = None

        metadata[key] = value
    return metadata



# TODO begin from here

def _check_cluster_exist(cs):
    pass


####################appnode#########################
@utils.arg('--vsm-os-username',
           metavar='<vsm-os-username>',
           help='The username of openstack keystone connected.')
@utils.arg('--vsm-os-password',
           metavar='<vsm-os-password>',
           help='The password of openstack keystone connected.')
@utils.arg('--vsm-os-tenant-name',
           metavar='<vsm-os-tenant-name>',
           help='The tenant name of openstack keystone connected.')
@utils.arg('--vsm-os-auth-url',
           metavar='<vsm-os-auth-url>',
           help='The auth url of openstack keystone connected.')
@utils.arg('--vsm-os-region-name',
           metavar='<vsm-os-region-name>',
           default='RegionOne',
           help='The region name of openstack keystone connected. Default=RegionOne.')
@utils.arg('--ssh-user',
           metavar='<ssh-user>',
           help='The ssh user to connect openstack keystone node.')
@utils.service_type('vsm')
def do_appnode_create(cs, args):
    """Creates an appnode."""
    if not args.vsm_os_username:
        raise exceptions.CommandError("you need specify a OpenStack username")
    if not args.vsm_os_password:
        raise exceptions.CommandError("you need specify a OpenStack password")
    if not args.vsm_os_tenant_name:
        raise exceptions.CommandError("you need specify a OpenStack tenant name")
    if not args.vsm_os_auth_url:
        raise exceptions.CommandError("you need specify a OpenStack auth url")
    if not args.ssh_user:
        raise exceptions.CommandError("you need specify a password-less user to "
                                      "connect the openstack")
    appnode = {
        'os_username': args.vsm_os_username,
        'os_password': args.vsm_os_password,
        'os_tenant_name': args.vsm_os_tenant_name,
        'os_auth_url': args.vsm_os_auth_url,
        'os_region_name': args.vsm_os_region_name,
        'ssh_user': args.ssh_user
    }
    try:
        cs.appnodes.create(appnode)
        print("Succeed to create appnode.")
    except:
        raise exceptions.CommandError("Failed to create appnode.")

@utils.service_type('vsm')
def do_appnode_list(cs, args):
    """Lists all appnodes."""
    appnodes = cs.appnodes.list(detailed=False, search_opts=None)
    columns = ["ID", "VSMApp ID", "SSH Status", "SSH User", "OS UserName",
               "OS Password", "OS Tenant Name", "OS Auth Url", "OS Region Name",
               "UUID"]
    utils.print_list(appnodes, columns)

@utils.arg('id',
           metavar='<id>',
           help='ID of appnode.')
@utils.service_type('vsm')
def do_appnode_delete(cs, args):
    """Deletes an appnode by id."""
    appnode = _find_appnode(cs, args.id)
    try:
        cs.appnodes.delete(appnode)
        print("Succeed to delete appnode.")
    except:
        raise exceptions.CommandError("Failed to delete appnode.")

@utils.arg('id',
           metavar='<id>',
           help='ID of appnode.')
@utils.arg('--vsm-os-username',
           metavar='<vsm-os-username>',
           help='The username of openstack keystone connected.')
@utils.arg('--vsm-os-password',
           metavar='<vsm-os-password>',
           help='The password of openstack keystone connected.')
@utils.arg('--vsm-os-tenant-name',
           metavar='<vsm-os-tenant-name>',
           help='The tenant name of openstack keystone connected.')
@utils.arg('--vsm-os-auth-url',
           metavar='<vsm-os-auth-url>',
           help='The auth url of openstack keystone connected.')
@utils.arg('--vsm-os-region-name',
           metavar='<vsm-os-region-name>',
           default='RegionOne',
           help='The region name of openstack keystone connected.')
@utils.arg('--ssh-user',
           metavar='<ssh-user>',
           help='The ssh user to connect openstack keystone node.')
@utils.service_type('vsm')
def do_appnode_update(cs, args):
    """Updates an appnode by id."""
    appnode = _find_appnode(cs, args.id)
    vsm_os_username = args.vsm_os_username or appnode.os_username
    vsm_os_password = args.vsm_os_password or appnode.os_password
    vsm_os_tenant_name = args.vsm_os_tenant_name or appnode.os_tenant_name
    vsm_os_auth_url = args.vsm_os_auth_url or appnode.os_auth_url
    vsm_os_region_name = args.vsm_os_region_name or appnode.os_region_name
    ssh_user = args.ssh_user or appnode.ssh_user
    ssh_status = ""
    log_info = ""
    new_appnode = {
        'os_username': vsm_os_username,
        'os_password': vsm_os_password,
        'os_tenant_name': vsm_os_tenant_name,
        'os_auth_url': vsm_os_auth_url,
        'os_region_name': vsm_os_region_name,
        'ssh_user': ssh_user,
        'ssh_status': ssh_status,
        'log_info': log_info
    }
    try:
        cs.appnodes.update(appnode, new_appnode)
        print("Succeed to update appnode.")
    except:
        raise exceptions.CommandError("Failed to update appnode.")


#####################cluster########################
@utils.arg('--name',
           metavar='<name>',
           default='default',
           help='Cluster name[Not used]. Default=default.')
@utils.arg('--file-system',
           metavar='<file-system>',
           default='xfs',
           help='File system[Not used]. Default=xfs.')
@utils.arg('--journal-size',
           metavar='<journal-size>',
           default='',
           help='File system[Not used]. Default="".')
@utils.arg('--size',
           metavar='<size>',
           default='',
           help='Size[Not used]. Default="".')
@utils.arg('--management-network',
           metavar='<management-network>',
           default='',
           help='Management network[Not used]. Default="".')
@utils.arg('--ceph-public-network',
           metavar='<ceph-public-network>',
           default='',
           help='Ceph public network[Not used]. Default="".')
@utils.arg('--cluster-network',
           metavar='<cluster-network>',
           default='',
           help='Cluster network[Not used]. Default="".')
@utils.arg('--primary-public-netmask',
           metavar='<primary-public-netmask>',
           default='',
           help='Primary public netmask[Not used]. Default="".')
@utils.arg('--secondary-public-netmask',
           metavar='<secondary-public-netmask>',
           default='',
           help='Secondary public netmask[Not used]. Default="".')
@utils.arg('--cluster-netmask',
           metavar='<cluster-netmask>',
           default='',
           help='Cluster netmask[Not used]. Default="".')
@utils.arg('--servers',
           metavar='<id=server-id,is-storage=boolean,is-monitor=boolean>',
           action='append',
           default=[],
           help='Servers to create ceph cluster, need 3 servers at least.'
                'Boolean value is True or False[Default=True].')
@utils.service_type('vsm')
def do_cluster_create(cs, args):
    """Creates a cluster."""
    servers_list = []
    servers = args.servers
    id_list = []
    for server in servers:
        key_value_list = server.split(",")
        ser = {}
        for key_value in key_value_list:
            key, _sep, value = key_value.partition("=")
            # is-storage -> is_storage
            # is-monitor -> is_monitor
            key = key.replace("-", "_")
            if key == "id":
                if value not in id_list:
                    id_list.append(value)
                else:
                    raise exceptions.CommandError("ID is duplicated")
            else:
                strutils.bool_from_string(value, default=True)
            ser[key] = value
        servers_list.append(ser)
    if len(servers_list) < 3:
        raise exceptions.CommandError("you need to specify 3 servers.")
    cs.clusters.create(servers=servers_list)
    print(servers_list)

@utils.arg('cluster',
           metavar='<cluster>',
           help='Name or ID of cluster.')
@utils.service_type('vsm')
def do_cluster_show(cs, args):
    """Shows details info of a cluster."""
    cluster = _find_cluster(cs, args.cluster)
    _print_cluster(cluster)

@utils.service_type('vsm')
def do_cluster_list(cs, args):
    """Lists all clusters."""
    clusters = cs.clusters.list(detailed=False, search_opts=None)
    columns = ["ID", "Name", "Size", "File System"]
    utils.print_list(clusters, columns)

# @utils.service_type('vsm')
# def do_cluster_delete(cs, args):
#     """Deletes a cluster."""
#     _is_developing("cluster-delete",
#                    "Deletes a cluster.")

# @utils.service_type('vsm')
# def do_cluster_update(cs, args):
#     """Updates a cluster."""
#     _is_developing("cluster-update",
#                    "Updates a cluster.")

@utils.service_type('vsm')
def do_cluster_summary(cs, args):
    """Gets summary info of a cluster."""
    cluster_summary = cs.clusters.summary()
    _print_cluster(cluster_summary)

# TODO not very good, should use service api to get service info
@utils.service_type('vsm')
def do_cluster_service_list(cs, args):
    """Lists all cluster services."""
    services = cs.clusters.get_service_list()
    columns = ["ID", "Binary", "Host", "Disabled", "Updated at"]
    utils.print_list(services, columns)

@utils.arg('--really-refresh',
           action='store_true',
           help='Really refresh the cluster status. Default=False.')
@utils.service_type('vsm')
def do_cluster_refresh(cs, args):
    """Refreshes cluster status."""
    if args.really_refresh:
        try:
            cs.clusters.refresh()
            print("Succeed to refresh cluster status.")
        except:
            raise exceptions.CommandError("Failed to refresh cluster status.")
    else:
        print("Follow with --really-refresh, if you really want to refresh the cluster status.")

# @utils.service_type('vsm')
# def do_cluster_import_ceph_conf(cs, args):
#     """Imports ceph conf."""
#     _is_developing("cluster-import-ceph-conf",
#                    "Imports ceph conf.")
#
# @utils.service_type('vsm')
# def do_cluster_import(cs, args):
#     """Imports an existing ceph cluster."""
#     _is_developing("cluster-import",
#                    "Imports an existing ceph cluster.")

@utils.arg('id',
           metavar='<id>',
           help='ID of cluster.')
@utils.service_type('vsm')
def do_cluster_stop(cs, args):
    """Stops ceph cluster."""
    try:
        cs.clusters.stop_cluster(args.id)
        print("Succeed to stop cluster.")
    except:
        raise exceptions.BadRequest("Failed to stop cluster.")


@utils.arg('id',
           metavar='<id>',
           help='ID of cluster.')
@utils.service_type('vsm')
def do_cluster_start(cs, args):
    """Starts ceph cluster."""
    try:
        cs.clusters.start_cluster(args.id)
        print("Succeed to start cluster.")
    except:
        raise exceptions.BadRequest("Failed to start cluster.")


####################device#########################
# @utils.service_type('vsm')
# def do_device_show(cs, args):
#     """Shows details info of a device."""
#     _is_developing("device-show",
#                    "Shows details info of a device.")

@utils.service_type('vsm')
def do_device_list(cs, args):
    """Lists all devices."""
    devices = cs.devices.list(detailed=False, search_opts=None)
    columns = ["ID", "Name", "Path", "Journal", "Device Type", "Used_Capacity_KB",
               "Avail_Capacity_KB", "Total_Capacity_KB", "State", "Journal State"]
    utils.print_list(devices, columns)

@utils.arg('server-id',
           metavar='<server-id>',
           help='ID of server.')
@utils.service_type('vsm')
def do_device_list_available_disks(cs, args):
    """Lists available disks."""
    search_opts = {
        'server_id': args.server_id,
        'result_mode': 'get_disks'
    }
    available_disks = cs.devices.get_available_disks(search_opts=search_opts)
    available_disks = available_disks['disks']
    columns = ["Disk Name", "By-Path", "By-UUID"]
    utils.print_list(available_disks, columns)

@utils.arg('--device-id',
           metavar='<device-id>',
           help='ID of device.')
@utils.arg('--device-path',
           metavar='<device-path>',
           help='Path of device.')
@utils.service_type('vsm')
def do_device_show_smart_info(cs, args):
    """Shows smart info of a device."""
    if not args.device_id:
        raise exceptions.CommandError("you need to specify a Device ID")
    if not args.device_path:
        raise exceptions.CommandError("you need to specify a Device path")
    search_opts = {
        'device_id': args.device_id,
        'device_path': args.device_path
    }
    smart_info = cs.devices.get_smart_info(search_opts=search_opts)
    _print_device(smart_info)


#####################mds########################
@utils.arg('mds',
           metavar='<mds>',
           help='Name or ID of mds.')
@utils.service_type('vsm')
def do_mds_show(cs, args):
    """Shows details info of a mds."""
    mds = _find_mds(cs, args.mds)
    _print_mds(mds)

@utils.service_type('vsm')
def do_mds_list(cs, args):
    """Lists all mdses."""
    mdses = cs.mdses.list(detailed=False, search_opts=None)
    columns = ["ID", "GID", "Name", "State", "Address", "Updated_at"]
    utils.print_list(mdses, columns)

# @utils.arg('mds',
#            metavar='<mds>',
#            help='Name or ID of mds.')
# @utils.service_type('vsm')
# def do_mds_restart(cs, args):
#     """Restarts mds."""
#     mds = utils.find_mds(cs, args.mds)
#     resp, body = cs.mdses.restart(mds)
#     code = resp.status_code
#     if code != 202:
#         raise exceptions.CommandError("Failed to restart mds.")

# @utils.service_type('vsm')
# def do_mds_delete(cs, args):
#     """Deletes mds by id."""
#     _is_developing("mds-delete",
#                    "Deletes mds by id.")

# @utils.service_type('vsm')
# def do_mds_restore(cs, args):
#     """Restores mds."""
#     _is_developing("mds-restore",
#                    "Restores mds.")

@utils.service_type('vsm')
def do_mds_summary(cs, args):
    """Gets summary info of mds."""
    mds_summary = cs.mdses.summary()
    _print_mds(mds_summary)


#####################mon########################
@utils.arg('mon',
           metavar='<mon>',
           help='Name or ID of mon.')
@utils.service_type('vsm')
def do_mon_show(cs, args):
    """Shows details info of a mon."""
    mon = _find_mon(cs, args.mon)
    _print_mon(mon)

@utils.service_type('vsm')
def do_mon_list(cs, args):
    """Lists all mons."""
    mons = cs.monitors.list(detailed=False, search_opts=None)
    columns = ["ID", "Name", "Address", "Health", "Details"]
    utils.print_list(mons, columns)

@utils.service_type('vsm')
def do_mon_summary(cs, args):
    """Gets summary info of mon."""
    mon_summary = cs.monitors.summary()
    _print_mon(mon_summary)

@utils.arg('mon',
           metavar='<mon>',
           help='Name or ID of mon.')
@utils.service_type('vsm')
def do_mon_restart(cs, args):
    """Restarts a mon by id."""
    mon = _find_mon(cs, args.mon)
    try:
        cs.monitors.restart(mon)
        print("Succeed to restart mon named %s." % mon.name)
    except:
        raise exceptions.CommandError("Failed to restart mon.")


#####################osd########################
@utils.arg('osd',
           metavar='<osd>',
           help='Name or ID of osd.')
@utils.service_type('vsm')
def do_osd_show(cs, args):
    """Shows details info of an osd."""
    osd = _find_osd(cs, args.osd)
    _print_osd(osd)

@utils.service_type('vsm')
def do_osd_list(cs, args):
    """Lists all osds."""
    osds = cs.osds.list(detailed=False, search_opts=None, paginate_opts=None)
    columns = ["ID", "OSD Name", "Weight", "State", "Operation Status",
               "Device ID", "Service ID", "Updated_at"]
    utils.print_list(osds, columns)

@utils.arg('osd',
           metavar='<osd>',
           help='Name or ID of osd.')
@utils.service_type('vsm')
def do_osd_restart(cs, args):
    """Restarts an osd by id."""
    osd = _find_osd(cs, args.osd)
    try:
        cs.osds.restart(osd)
        print("Succeed to restart osd named %s." % osd.osd_name)
    except:
        raise exceptions.CommandError("Failed to restart osd.")

@utils.arg('osd',
           metavar='<osd>',
           help='Name or ID of osd.')
@utils.service_type('vsm')
def do_osd_remove(cs, args):
    """Removes an osd by id."""
    osd = _find_osd(cs, args.osd)
    try:
        cs.osds.remove(osd)
        print("Succeed to remove osd named %s." % osd.osd_name)
    except:
        raise exceptions.CommandError("Failed to remove osd.")

@utils.arg('--server-id',
           metavar='<server-id>',
           help='The id of server which to add new osd.')
@utils.arg('--storage-group-id',
           metavar='<storage-group-id>',
           help='The id of storage group.')
@utils.arg('--weight',
           metavar='<weight>',
           default='1.0',
           help='Weight of osd.')
@utils.arg('--journal',
           metavar='<journal>',
           help='Journal path.')
@utils.arg('--data',
           metavar='<data>',
           help='Data path.')
@utils.service_type('vsm')
def do_osd_add_new(cs, args):
    """Adds new osd to ceph cluster."""
    if not args.server_id:
        raise exceptions.CommandError("you need to specify a Server ID")
    if not args.storage_group_id:
        raise exceptions.CommandError("you need to specify a Storage Group ID")
    if not args.journal:
        raise exceptions.CommandError("you need to specify a journal")
    if not args.data:
        raise exceptions.CommandError("you need to specify a data")
    body = {
        'server_id': args.server_id,
        'osd_info': [
            {
                'storage_group_id': args.storage_group_id,
                'weight': args.weight,
                'journal': args.journal,
                'data': args.data
            }
        ]
    }
    try:
        cs.osds.add_new_disks_to_cluster(body=body)
        print("Succeed to add new osd to cluster.")
    except:
        raise exceptions.CommandError("Failed to add new osd to cluster.")

@utils.arg('osd',
           metavar='<osd>',
           help='Name or ID of osd.')
@utils.service_type('vsm')
def do_osd_restore(cs, args):
    """Restores an osd."""
    osd = _find_osd(cs, args.osd)
    try:
        cs.osds.restore(osd)
        osd = _find_osd(cs, args.osd)
        print("Succeed to restore osd named %s." % osd.osd_name)
    except:
        raise exceptions.CommandError("Failed to restore osd.")

@utils.service_type('vsm')
def do_osd_refresh(cs, args):
    """Refreshes osd."""
    try:
        cs.osds.refresh()
        print("Succeed to refresh osd status.")
    except:
        raise exceptions.CommandError("Failed to refresh osd status.")

@utils.service_type('vsm')
def do_osd_summary(cs, args):
    """Gets summary info of osd."""
    osd_summary = cs.osds.summary()
    _print_osd(osd_summary)


###################performance metric##########################
# @utils.service_type('vsm')
# def do_perf_metric_list(cs, args):
#     """Lists performance metrics."""
#     _is_developing("perf-metric-list",
#                    "Lists performance metrics.")


###################placement group##########################
@utils.arg('pg',
           metavar='<pg>',
           help='Name or ID of pg.')
@utils.service_type('vsm')
def do_pg_show(cs, args):
    """Shows details info of a placement group."""
    pg = _find_pg(cs, args.pg)
    _print_pg(pg)

@utils.service_type('vsm')
def do_pg_list(cs, args):
    """Lists all placement groups."""
    pgs = cs.placement_groups.list(detailed=False, search_opts=None, paginate_opts=None)
    columns = ["ID", "PG ID", "State", "UP", "Acting"]
    utils.print_list(pgs, columns)

@utils.service_type('vsm')
def do_pg_summary(cs, args):
    """Gets summary info of placement group."""
    pg_summary = cs.placement_groups.summary()
    _print_pg(pg_summary)


###################pool usage##########################
@utils.arg('--pools',
           metavar='<pool-id=pool-id,cinder-volume-host=hostname,appnode-id=appnode-id>',
           action='append',
           default=[],
           help='Each should have pool id, cinder volume host and appnode id.')
@utils.service_type('vsm')
def do_pool_usage_create(cs, args):
    """Creates pool usage."""
    pools_list = []
    pools = args.pools
    id_list = []
    for pool in pools:
        key_value_list = pool.split(",")
        po = {}
        for key_value in key_value_list:
            key, _sep, value = key_value.partition("=")
            # pool-id -> pool_id
            # cinder-volume-host -> cinder_volume_host
            # appnode-id -> appnode_id
            key = key.replace("-", "_")
            if key == "pool_id":
                if value not in id_list:
                    id_list.append(value)
                else:
                    raise exceptions.CommandError("Pool id is duplicated")
            po[key] = value
        pools_list.append(po)
    cs.pool_usages.create(pools=pools_list)

@utils.service_type('vsm')
def do_pool_usage_list(cs, args):
    """Lists all pool usages."""
    pool_usages = cs.pool_usages.list(detailed=False, search_opts=None)
    columns = ["ID", "Pool ID", "VSMApp ID", "Cinder Volume Host", "Attach Status",
               "Attach_at"]
    utils.print_list(pool_usages, columns)


###################rbd pool##########################
# @utils.arg('rbd',
#            metavar='<rbd>',
#            help='Name or ID of rbd.')
# @utils.service_type('vsm')
# def do_rbd_pool_show(cs, args):
#     """Shows details info of rbd pool."""
#     rbd = _find_rbd(cs, args.rbd)
#     _print_rbd(rbd)

@utils.service_type('vsm')
def do_rbd_pool_list(cs, args):
    """Lists all rbd pools."""
    rbds = cs.rbd_pools.list(detailed=True, search_opts=None, paginate_opts=None)
    columns = ["ID", "Pool", "Image Name", "Size", "Objects", "Order",
               "Format", "Updated_at"]
    utils.print_list(rbds, columns)

@utils.service_type('vsm')
def do_rbd_pool_summary(cs, args):
    """Gets summary info of rbd pool."""
    rbd_summary = cs.rbd_pools.summary()
    _print_rbd(rbd_summary)


###################server##########################
@utils.arg('server',
           metavar='<server>',
           help='Name or ID of server.')
@utils.service_type('vsm')
def do_server_show(cs, args):
    """Shows details info of server."""
    server = _find_server(cs, args.server)
    _print_server(server)

@utils.service_type('vsm')
def do_server_list(cs, args):
    """Lists all servers."""
    result = cs.servers.list()
    columns = ["ID", "HOST", "Type", "Zone ID", "Service ID",
               "Cluster IP", "Secondary Public IP", "Primary Public IP",
               "Raw IP", "Ceph Ver", "OSDs", "Status"]
    utils.print_list(result, columns)

@utils.service_type('vsm')
def do_server_add(cs, args):
    """\033[1;31;40mAdds a new server.\033[0m"""
    _is_developing("server-add",
                   "Adds a new server.")

@utils.arg('--id',
           metavar='<id>',
           action='append',
           default=[],
           help='ID of server.')
@utils.service_type('vsm')
def do_server_remove(cs, args):
    """Removes a server."""
    if not args.id:
        raise exceptions.CommandError("you need to specify Server ID")
    remove_storage = True
    remove_monitor = True
    cluster_id = 1
    servers = []
    for id in args.id:
        servers.append({
            'id': id,
            'cluster_id': cluster_id,
            'remove_monitor': remove_monitor,
            'remove_storage': remove_storage
        })
    try:
        cs.servers.remove(servers)
        print("Succeed to remove servers.")
    except:
        raise exceptions.CommandError("Failed to remove servers.")

@utils.arg('--id',
           metavar='<id>',
           action='append',
           default=[],
           help='ID of server.')
@utils.service_type('vsm')
def do_server_start(cs, args):
    """Starts a server."""
    if not args.id:
        raise exceptions.CommandError("you need to specify Server ID")
    cluster_id = 1
    servers = []
    for id in args.id:
        servers.append({
            'id': id,
            'cluster_id': cluster_id
        })
    try:
        cs.servers.start(servers)
        print("Succeed to start servers.")
    except:
        raise exceptions.CommandError("Failed to start servers.")

@utils.arg('--id',
           metavar='<id>',
           action='append',
           default=[],
           help='ID of server.')
@utils.service_type('vsm')
def do_server_stop(cs, args):
    """Stops a server."""
    if not args.id:
        raise exceptions.CommandError("you need to specify Server ID")
    cluster_id = 1
    servers = []
    for id in args.id:
        servers.append({
            'id': id,
            'cluster_id': cluster_id
        })
    try:
        cs.servers.stop(servers)
        print("Succeed to stop servers.")
    except:
        raise exceptions.CommandError("Failed to stop servers.")

# @utils.service_type('vsm')
# def do_server_ceph_upgrade(cs, args):
#     """Upgrades ceph version."""
#     _is_developing("server-ceph-upgrade",
#                    "Upgrades ceph version.")


###################storage group##########################
# @utils.service_type('vsm')
# def do_storage_group_create(cs, args):
#     """Creates storage group."""
#     _is_developing("storage-group-create",
#                    "Creates storage group.")

@utils.arg('id',
           metavar='<id>',
           help='ID of storage group.')
@utils.service_type('vsm')
def do_storage_group_show(cs, args):
    """Shows detail info of storage group."""
    storage_group = _find_storage_group(cs, args.id)
    _print_storage_group(storage_group)

@utils.service_type('vsm')
def do_storage_group_list(cs, args):
    """Lists all storage groups."""
    storage_groups = cs.storage_groups.list(detailed=True, search_opts=None)
    columns = ["ID", "Name", "Storage Class", "Attached OSDs", "Rule ID",
               "Status", "Capacity Used", "Capacity Total"]
    utils.print_list(storage_groups, columns)

@utils.service_type('vsm')
def do_storage_group_summary(cs, args):
    """Gets summary info of storage group."""
    storage_group_summary = cs.storage_groups.summary()
    _print_storage_group(storage_group_summary)


###################storage pool##########################
@utils.arg('storage-pool',
           metavar='<storage-pool>',
           help='Name or ID of storage pool.')
@utils.service_type('vsm')
def do_storage_pool_show(cs, args):
    """Shows details info of storage pool."""
    storage_pool = _find_storage_pool(cs, args.storage_pool)
    _print_storage_pool(storage_pool)

@utils.arg('name',
           metavar='<name>',
           help='Name of storage pool.')
@utils.arg('--storage-group-id',
           metavar='<storage-group-id>',
           help='ID of storage group.')
@utils.arg('--pg-num',
           metavar='<pg-num>',
           help='Placement group number.')
@utils.arg('--pool-quota',
           metavar='<pool-quota>',
           default=0,
           help='Pool quota. Default=0.')
@utils.arg('--cluster-id',
           metavar='<cluster-id>',
           default=0,
           help='Pool quota. Default=0.')
@utils.arg('--tag',
           metavar='<tag>',
           default="",
           help='Tag. Default=Name of pool.')
@utils.service_type('vsm')
def do_storage_pool_replicated_create(cs, args):
    """Creates replicated pool."""
    if not args.storage_group_id:
        raise exceptions.CommandError("you need to specify a Storage Group ID")
    if not args.pg_num:
        raise exceptions.CommandError("you need to specify a pg number")
    storage_group = _find_storage_group(cs, args.storage_group_id)
    tag = args.tag
    pool_name = args.name
    if not tag:
        tag = pool_name
    pool_quota = args.pool_quota
    if pool_quota:
        enable_pool_quota = True
    else:
        enable_pool_quota = False
    pool = {
        "pool": {
            "name": pool_name,
            "storageGroupId": args.storage_group_id,
            "storageGroupName": storage_group.name,
            "auto_growth_pg": args.pg_num,
            "enablePoolQuota": enable_pool_quota,
            "poolQuota": pool_quota,
            "clusterId": args.cluster_id,
            "replicatedStorageGroupId": "replica",
            "tag": tag,
            "createdBy": "VSM"
        }
    }
    try:
        cs.vsms.create_storage_pool(pool)
        print("Succeed to create replicated storage pool.")
    except:
        raise exceptions.CommandError("Failed to create replicated storage pool.")

@utils.arg('name',
           metavar='<name>',
           help='Name of storage pool.')
@utils.arg('--storage-group-id',
           metavar='<storage-group-id>',
           help='ID of storage group.')
@utils.arg('--ec-failure-domain',
           metavar='<ec-failure-domain>',
           help='EC failure domain[osd, host or zone].')
@utils.arg('--pool-quota',
           metavar='<pool-quota>',
           default=0,
           help='Pool quota. Default=0')
@utils.arg('--cluster-id',
           metavar='<cluster-id>',
           default=0,
           help='Pool quota. Default=0')
@utils.arg('--tag',
           metavar='<tag>',
           default="",
           help='Tag. Default=Name of pool.')
@utils.arg('--ec-profile-id',
           metavar='<ec-profile-id>',
           default=1,
           help='Tag. Default=1.')
@utils.service_type('vsm')
def do_storage_pool_ec_create(cs, args):
    """Creates ec pool."""
    if not args.storage_group_id:
        raise exceptions.CommandError("you need to specify a Storage Group ID")
    if not args.ec_failure_domain:
        raise exceptions.CommandError("you need to specify a EC Failure Domain")
    storage_group = _find_storage_group(cs, args.storage_group_id)
    tag = args.tag
    pool_name = args.name
    if not tag:
        tag = pool_name
    pool_quota = args.pool_quota
    if pool_quota:
        enable_pool_quota = True
    else:
        enable_pool_quota = False
    EC_FAILURE_DOMAIN = ['osd', 'host', 'zone']
    ec_failure_domain = args.ec_failure_domain
    if ec_failure_domain not in EC_FAILURE_DOMAIN:
        raise exceptions.CommandError("--ec-failure-domain should be on of osd, host or zone")
    pool = {
        "pool": {
            "name": pool_name,
            "storageGroupId": args.storage_group_id,
            "storageGroupName": storage_group.name,
            "tag": tag,
            "clusterId": args.cluster_id,
            "createdBy": "VSM",
            "ecProfileId": args.ec_profile_id,
            "ecFailureDomain": ec_failure_domain,
            "enablePoolQuota": enable_pool_quota,
            "poolQuota": pool_quota
        }
    }
    try:
        cs.vsms.create_storage_pool(pool)
        print("Succeed to create ec storage pool.")
    except:
        raise exceptions.CommandError("Failed to create ec storage pool.")

@utils.service_type('vsm')
def do_storage_pool_list(cs, args):
    """Lists all storage pools."""
    storage_pools = cs.storage_pools.list(detailed=True, search_opts=None)
    _translate_storage_pool_keys(storage_pools)
    columns = ["ID", "Name", "Pool ID", "PG Num", "PGP Num", "Cluster ID", "Status",
               "Storage Group", "Tag", "Quota", "Size", "Updated_at"]
    utils.print_list(storage_pools, columns)

@utils.arg('--storage-pool-id',
           metavar='<storage-pool-id>',
           help='Pool id of storage pool as the storage pool of cache tier pool.')
@utils.arg('--cache-pool-id',
           metavar='<cache-pool-id>',
           help='Pool id of storage pool as the cache pool of cache tier pool.')
@utils.arg('--cache-mode',
           metavar='<cache-mode>',
           default='readonly',
           help='Mode of cache tier pool[readonly or writeback]. Default=readonly.')
@utils.arg('--force-nonempty',
           action='store_true',
           help='Force nonempty. Default=False.')
@utils.arg('--hit-set-type',
           metavar='<hit-set-type>',
           default='bloom',
           help='Hit set type. Default=bloom.')
@utils.arg('--hit-set-count',
           metavar='<hit-set-count>',
           default=1,
           help='Hit set count. Default=1.')
@utils.arg('--hit-set-period-s',
           metavar='<hit-set-period-s>',
           default=3600,
           help='Hit set period(s). Default=3600.')
@utils.arg('--target-max-mem-mb',
           metavar='<target-max-mem-mb>',
           default=1000000,
           help='Target max mem(mb). Default=1000000.')
@utils.arg('--target-dirty-ratio',
           metavar='<target-dirty-ratio>',
           default=0.4,
           help='Target dirty ratio. Default=0.4.')
@utils.arg('--target-full-ratio',
           metavar='<target-full-ratio>',
           default=0.8,
           help='Target full ratio. Default=0.8.')
@utils.arg('--target-max-objects',
           metavar='<target-max-objects>',
           default=1000000,
           help='Target max objects. Default=1000000.')
@utils.arg('--target-min-flush-age-m',
           metavar='<target-min-flush-age-m>',
           default=10,
           help='Target min flush age(m). Default=10.')
@utils.arg('--target-min-evict-age-m',
           metavar='<target-min-evict-age-m>',
           default=20,
           help='Target min evict age(m). Default=20.')
@utils.service_type('vsm')
def do_storage_pool_add_cache_tier(cs, args):
    """Adds cache tier pool."""
    if not args.storage_pool_id:
        raise exceptions.CommandError("you need to specify a Storage Pool ID")
    if not args.cache_pool_id:
        raise exceptions.CommandError("you need to specify a Cache Pool ID")
    storage_pool_id = args.storage_pool_id
    cache_pool_id = args.cache_pool_id
    if storage_pool_id == cache_pool_id:
        raise exceptions.CommandError("Storage pool id can not be same as cache pool id.")
    storage_pool = _find_storage_pool(cs, storage_pool_id)
    cache_pool = _find_storage_pool(cs, cache_pool_id)

    cache_tier = {
        "cache_tier": {
            "storage_pool_id": storage_pool.id,
            "cache_pool_id": cache_pool.id,
            "cache_mode": args.cache_mode,
            "force_nonempty": args.force_nonempty,
            "options": {
                "hit_set_type": args.hit_set_type,
                "hit_set_count": args.hit_set_count,
                "hit_set_period_s": args.hit_set_period_s,
                "target_max_mem_mb": args.target_max_mem_mb,
                "target_dirty_ratio": args.target_dirty_ratio,
                "target_full_ratio": args.target_full_ratio,
                "target_max_objects": args.target_max_objects,
                "target_min_flush_age_m": args.target_min_flush_age_m,
                "target_min_evict_age_m": args.target_min_evict_age_m
            }
        }
    }
    try:
        cs.storage_pools.add_cache_tier(cache_tier)
        print("Succeed to add cache tier.")
    except:
        raise exceptions.CommandError("Failed to add cache tier.")

@utils.arg('id',
           metavar='<id>',
           help='Pool id of storage pool as cache.')
@utils.service_type('vsm')
def do_storage_pool_remove_cache_tier(cs, args):
    """Removes cache tier pool."""
    try:
        body = {
            "cache_tier": {
                "cache_pool_id": args.id
            }
        }
        cs.storage_pools.remove_cache_tier(body)
        print("Succeed to remove cache tier pool.")
    except:
        raise exceptions.CommandError("Failed to remove cache tier pool.")

@utils.service_type('vsm')
def do_storage_pool_list_ec_profiles(cs, args):
    """Lists ec profiles."""
    ec_profiles = cs.storage_pools.ec_profiles()
    columns = ["ID", "Name"]
    utils.print_list(ec_profiles, columns)


###################setting##########################
@utils.arg('setting-name',
           metavar='<setting-name>',
           help='Name of setting.')
@utils.service_type('vsm')
def do_setting_show(cs, args):
    """Shows details info of setting."""
    setting = cs.vsm_settings.get(args.setting_name)
    _print_setting(setting)

@utils.service_type('vsm')
def do_setting_list(cs, args):
    """Lists all settings."""
    settings = cs.vsm_settings.list(detailed=False, search_opts=None)
    columns = ["ID", "Name", "Value"]
    utils.print_list(settings, columns)

@utils.arg('name',
           metavar='<name>',
           help='Name of setting.')
@utils.arg('--value',
           metavar='<value>',
           help='Value of setting.')
@utils.service_type('vsm')
def do_setting_create(cs, args):
    """Creates a setting[if exist, for updating]."""
    setting = {
        "name": args.name,
        "value": args.value
    }
    try:
        cs.vsm_settings.create(setting)
        print("Succeed to create or update setting.")
    except:
        raise exceptions.CommandError("Failed to create or update setting.")


###################zone##########################
@utils.service_type('vsm')
def do_zone_list(cs, args):
    """Lists all zones."""
    zones = cs.zones.list(detailed=False, search_opts=None)
    columns = ["ID", "Name"]
    utils.print_list(zones, columns)


###################rgw##########################
@utils.arg('--host',
           metavar='<host>',
           help='The host of rgw.')
@utils.arg('--name',
           metavar='<name>',
           default="radosgw.gateway",
           help='The name of rgw instance. Default=radosgw.gateway.')
@utils.arg('--is-ssl',
           action='store_true',
           help='SSL of not. Default=False.')
@utils.arg('--uid',
           metavar='<uid>',
           default="johndoe",
           help='The user name. Default=johndoe.')
@utils.arg('--display-name',
           metavar='<display-name>',
           default="John Doe",
           help='The user display name. Default=John Doe.')
@utils.arg('--email',
           metavar='<email>',
           default="john@example.comjohn@example.com",
           help='The Email. Default=john@example.comjohn@example.com.')
@utils.arg('--sub-user',
           metavar='<sub-user>',
           default="johndoe:swift",
           help='The sub user name. Default=johndoe:swift.')
@utils.arg('--access',
           metavar='<access>',
           default="full",
           help='The access type. Default=full.')
@utils.arg('--key-type',
           metavar='<key-type>',
           default="swift",
           help='The key type. Default=swift.')
@utils.service_type('vsm')
def do_rgw_create(cs, args):
    """Creates a rgw."""
    host = args.host
    if not host:
        raise exceptions.CommandError("you need specify a host")
    rgw_instance_name = args.name
    is_ssl = args.is_ssl
    uid = args.uid
    display_name = args.display_name
    email = args.email
    sub_user = args.sub_user
    access = args.access
    key_type = args.key_type
    try:
        cs.rgws.create(host, rgw_instance_name, is_ssl, uid, display_name, email,
                       sub_user, access, key_type)
        print("Succeed to create rgw.")
    except:
        raise exceptions.CommandError("Failed to create rgw.")


# TODO tag for those not completed commands
# It will be removed later
def _is_developing(method, message):
    print('\033[1;31;40m')
    print('*' * 50)
    print('*Method:\t%s' % method)
    print('*Description:\t%s' % message)
    print('*Status:\t%s' % "Not Completed Now!")
    print('*' * 50)
    print('\033[0m')