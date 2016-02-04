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

import argparse
import os
import sys
import time

from vsmclient import exceptions
from vsmclient import utils

def _poll_for_status(poll_fn, obj_id, action, final_ok_states,
                     poll_period=5, show_progress=True):
    """Block while an action is being performed, periodically printing
    progress.
    """
    def print_progress(progress):
        if show_progress:
            msg = ('\rInstance %(action)s... %(progress)s%% complete'
                   % dict(action=action, progress=progress))
        else:
            msg = '\rInstance %(action)s...' % dict(action=action)

        sys.stdout.write(msg)
        sys.stdout.flush()

    print
    while True:
        obj = poll_fn(obj_id)
        status = obj.status.lower()
        progress = getattr(obj, 'progress', None) or 0
        if status in final_ok_states:
            print_progress(100)
            print "\nFinished"
            break
        elif status == "error":
            print "\nError %(action)s instance" % locals()
            break
        else:
            print_progress(progress)
            time.sleep(poll_period)

def _find_vsm(cs, vsm):
    """Get a vsm by ID."""
    return utils.find_resource(cs.vsms, vsm)

def _find_vsm_snapshot(cs, snapshot):
    """Get a vsm snapshot by ID."""
    return utils.find_resource(cs.vsm_snapshots, snapshot)

def _find_backup(cs, backup):
    """Get a backup by ID."""
    return utils.find_resource(cs.backups, backup)

def _print_vsm(vsm):
    utils.print_dict(vsm._info)

def _print_vsm_snapshot(snapshot):
    utils.print_dict(snapshot._info)

def _translate_keys(collection, convert):
    for item in collection:
        keys = item.__dict__.keys()
        for from_key, to_key in convert:
            if from_key in keys and to_key not in keys:
                setattr(item, to_key, item._info[from_key])

def _translate_vsm_keys(collection):
    convert = [('displayName', 'display_name'), ('vsmType', 'vsm_type')]
    _translate_keys(collection, convert)

def _translate_vsm_snapshot_keys(collection):
    convert = [('displayName', 'display_name'), ('vsmId', 'vsm_id')]
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
           help='The region name of openstack keystone connected.')
@utils.arg('--ssh-user',
           metavar='<ssh-user>',
           help='The ssh user to connect openstack keystone node.')
@utils.service_type('vsm')
def do_appnode_create(cs, args):
    """\033[1;32;40mCreates an appnode.\033[0m"""
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
    """\033[1;32;40mLists all appnodes.\033[0m"""
    appnodes = cs.appnodes.list(detailed=False, search_opts=None)
    columns = ["ID", "VSMApp ID", "SSH Status", "SSH User", "OS UserName",
               "OS Password", "OS Tenant Name", "OS Auth Url", "OS Region Name",
               "UUID"]
    utils.print_list(appnodes, columns)

@utils.arg('appnode',
           metavar='<appnode>',
           help='Name or ID of appnode.')
@utils.service_type('vsm')
def do_appnode_delete(cs, args):
    """\033[1;32;40mDeletes an appnode by id.\033[0m"""
    appnode = utils.find_appnode(cs, args.appnode)
    try:
        cs.appnodes.delete(appnode)
        print("Succeed to delete appnode.")
    except:
        raise exceptions.CommandError("Failed to delete appnode.")

@utils.service_type('vsm')
def do_appnode_update(cs, args):
    """Updates an appnode by id."""
    _is_developing("appnode-update",
                   "Updates an appnode by id.")


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
                'Boolean value is True or False.')
@utils.service_type('vsm')
def do_cluster_create(cs, args):
    """\033[1;32;40mCreates a cluster.\033[0m"""
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
                if value != "False" and value != "True":
                    raise exceptions.CommandError("is-monitor or is-storage is not True or False")
                elif value == "False":
                    value = False
                elif value == "True":
                    value = True
            ser[key] = value
        servers_list.append(ser)
    if len(servers_list) < 3:
        raise exceptions.CommandError("servers is less than 3.")
    cs.clusters.create(servers=servers_list)
    print(servers_list)

@utils.arg('cluster',
           metavar='<cluster>',
           help='Name or ID of cluster.')
@utils.service_type('vsm')
def do_cluster_show(cs, args):
    """\033[1;32;40mShows details info of a cluster.\033[0m"""
    info = dict()
    cluster = utils.find_cluster(cs, args.cluster)
    info.update(cluster._info)
    utils.print_dict(info)

@utils.service_type('vsm')
def do_cluster_list(cs, args):
    """\033[1;32;40mLists all clusters.\033[0m"""
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
    """\033[1;32;40mGets summary info of a cluster.\033[0m"""
    info = cs.clusters.summary()
    info = info._info
    utils.print_dict(info)

# TODO not very good, should use service api to get service info
@utils.service_type('vsm')
def do_cluster_service_list(cs, args):
    """\033[1;32;40mLists all cluster services.\033[0m"""
    services = cs.clusters.get_service_list()
    columns = ["ID", "Binary", "Host", "Disabled", "Updated at"]
    utils.print_list(services, columns)

@utils.service_type('vsm')
def do_cluster_refresh(cs, args):
    """\033[1;32;40mRefreshes cluster status.\033[0m"""
    try:
        cs.clusters.refresh()
        print("Succeed to refresh cluster status.")
    except:
        raise exceptions.CommandError("Failed to refresh cluster status.")

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
    """\033[1;32;40mStops ceph cluster.\033[0m"""
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
    """\033[1;32;40mStarts ceph cluster.\033[0m"""
    try:
        cs.clusters.start_cluster(args.id)
        print("Succeed to start cluster.")
    except:
        raise exceptions.BadRequest("Failed to start cluster.")


####################device#########################
# @utils.service_type('vsm')
# def do_device_show(cs, args):
#     """\033[1;32;40mShows details info of a device.\033[0m"""
#     _is_developing("device-show",
#                    "Shows details info of a device.")

@utils.service_type('vsm')
def do_device_list(cs, args):
    """\033[1;32;40mLists all devices.\033[0m"""
    devices = cs.devices.list(detailed=False, search_opts=None)
    columns = ["ID", "Name", "Path", "Journal", "Device Type", "Used_Capacity_KB",
               "Avail_Capacity_KB", "Total_Capacity_KB", "State", "Journal State"]
    utils.print_list(devices, columns)

@utils.arg('--server-id',
           metavar='<server-id>',
           help='ID of server.')
@utils.service_type('vsm')
def do_device_list_available_disks(cs, args):
    """\033[1;32;40mLists available disks.\033[0m"""
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
    """\033[1;32;40mShows smart info of a device.\033[0m"""
    search_opts = {
        'device_id': args.device_id,
        'device_path': args.device_path
    }
    smart_info = cs.devices.get_smart_info(search_opts=search_opts)
    utils.print_dict(smart_info)


#####################mds########################
@utils.arg('mds',
           metavar='<mds>',
           help='Name or ID of mds.')
@utils.service_type('vsm')
def do_mds_show(cs, args):
    """\033[1;32;40mShows details info of a mds.\033[0m"""
    info = dict()
    mds = utils.find_mds(cs, args.mds)
    info.update(mds._info)
    utils.print_dict(info)

@utils.service_type('vsm')
def do_mds_list(cs, args):
    """\033[1;32;40mLists all mdses.\033[0m"""
    mdses = cs.mdses.list(detailed=False, search_opts=None)
    columns = ["ID", "GID", "Name", "State", "Address", "Updated_at"]
    utils.print_list(mdses, columns)

# @utils.arg('mds',
#            metavar='<mds>',
#            help='Name or ID of mds.')
# @utils.service_type('vsm')
# def do_mds_restart(cs, args):
#     """\033[1;32;40mRestarts mds.\033[0m"""
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
    """\033[1;32;40mGets summary info of mds.\033[0m"""
    info = cs.mdses.summary()
    info = info._info
    utils.print_dict(info)


#####################mon########################
@utils.arg('mon',
           metavar='<mon>',
           help='Name or ID of mon.')
@utils.service_type('vsm')
def do_mon_show(cs, args):
    """\033[1;32;40mShows details info of a mon.\033[0m"""
    info = dict()
    mon = utils.find_mon(cs, args.mon)
    info.update(mon._info)
    utils.print_dict(info)

@utils.service_type('vsm')
def do_mon_list(cs, args):
    """\033[1;32;40mLists all mons.\033[0m"""
    mons = cs.monitors.list(detailed=False, search_opts=None)
    columns = ["ID", "Name", "Address", "Health", "Details"]
    utils.print_list(mons, columns)

@utils.service_type('vsm')
def do_mon_summary(cs, args):
    """\033[1;32;40mGets summary info of mon.\033[0m"""
    info = cs.monitors.summary()
    info = info._info
    utils.print_dict(info)

@utils.arg('id',
           metavar='<id>',
           help='ID of mon.')
@utils.service_type('vsm')
def do_mon_restart(cs, args):
    """\033[1;32;40mRestarts a mon by id.\033[0m"""
    mon = utils.find_mon(cs, args.id)
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
    """\033[1;32;40mShows details info of an osd.\033[0m"""
    info = dict()
    osd = utils.find_osd(cs, args.osd)
    info.update(osd._info)
    utils.print_dict(info)

@utils.service_type('vsm')
def do_osd_list(cs, args):
    """\033[1;32;40mLists all osds.\033[0m"""
    osds = cs.osds.list(detailed=False, search_opts=None, paginate_opts=None)
    columns = ["ID", "OSD Name", "Weight", "State", "Operation Statue",
               "Device ID", "Service ID", "Updated_at"]
    utils.print_list(osds, columns)

@utils.arg('id',
           metavar='<id>',
           help='ID of osd.')
@utils.service_type('vsm')
def do_osd_restart(cs, args):
    """\033[1;32;40mRestarts an osd by id.\033[0m"""
    osd = utils.find_osd(cs, args.id)
    try:
        cs.osds.restart(osd)
        print("Succeed to restart osd named %s." % osd.osd_name)
    except:
        raise exceptions.CommandError("Failed to restart osd.")

@utils.arg('id',
           metavar='<id>',
           help='ID of osd.')
@utils.service_type('vsm')
def do_osd_remove(cs, args):
    """\033[1;32;40mRemoves an osd by id.\033[0m"""
    osd = utils.find_osd(cs, args.id)
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
    """\033[1;32;40mAdds new osd to ceph cluster.\033[0m"""
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

@utils.arg('id',
           metavar='<id>',
           help='ID of osd.')
@utils.service_type('vsm')
def do_osd_restore(cs, args):
    """\033[1;32;40mRestores an osd.\033[0m"""
    osd = utils.find_osd(cs, args.id)
    try:
        cs.osds.restore(osd)
        osd = utils.find_osd(cs, args.id)
        print("Succeed to restore osd named %s." % osd.osd_name)
    except:
        raise exceptions.CommandError("Failed to restore osd.")

@utils.service_type('vsm')
def do_osd_refresh(cs, args):
    """\033[1;32;40mRefreshes osd.\033[0m"""
    try:
        cs.osds.refresh()
        print("Succeed to refresh osd status.")
    except:
        raise exceptions.CommandError("Failed to refresh osd status.")

@utils.service_type('vsm')
def do_osd_summary(cs, args):
    """\033[1;32;40mGets summary info of osd.\033[0m"""
    info = cs.osds.summary()
    info = info._info
    utils.print_dict(info)


###################performance metric##########################
@utils.service_type('vsm')
def do_perf_metric_list(cs, args):
    """Lists performance metrics."""
    _is_developing("perf-metric-list",
                   "Lists performance metrics.")


###################placement group##########################
@utils.arg('pg',
           metavar='<pg>',
           help='Name or ID of pg.')
@utils.service_type('vsm')
def do_pg_show(cs, args):
    """\033[1;32;40mShows details info of a placement group.\033[0m"""
    info = dict()
    pg = utils.find_pg(cs, args.pg)
    info.update(pg._info)
    utils.print_dict(info)

@utils.service_type('vsm')
def do_pg_list(cs, args):
    """\033[1;32;40mLists all placement groups.\033[0m"""
    pgs = cs.placement_groups.list(detailed=False, search_opts=None, paginate_opts=None)
    columns = ["ID", "PG ID", "State", "UP", "Acting"]
    utils.print_list(pgs, columns)

@utils.service_type('vsm')
def do_pg_summary(cs, args):
    """\033[1;32;40mGets summary info of placement group.\033[0m"""
    info = cs.placement_groups.summary()
    info = info._info
    utils.print_dict(info)


###################pool usage##########################
@utils.service_type('vsm')
def do_pool_usage_create(cs, args):
    """Creates pool usage."""
    _is_developing("pool-usage-create",
                   "Creates pool usage.")

@utils.service_type('vsm')
def do_pool_usage_list(cs, args):
    """\033[1;32;40mLists all pool usages.\033[0m"""
    pool_usages = cs.pool_usages.list(detailed=False, search_opts=None)
    columns = ["ID", "Pool ID", "VSMApp ID", "Cinder Volume Host", "Attach Status",
               "Attach_at"]
    utils.print_list(pool_usages, columns)


###################rbd pool##########################
@utils.arg('rbd',
           metavar='<rbd>',
           help='Name or ID of rbd.')
@utils.service_type('vsm')
def do_rbd_pool_show(cs, args):
    """\033[1;32;40mShows details info of rbd pool.\033[0m"""
    info = dict()
    rbd = utils.find_rbd(cs, args.rbd)
    info.update(rbd._info)
    utils.print_dict(info)

@utils.service_type('vsm')
def do_rbd_pool_list(cs, args):
    """\033[1;32;40mLists all rbd pools.\033[0m"""
    rbds = cs.rbd_pools.list(detailed=False, search_opts=None, paginate_opts=None)
    columns = ["ID"]
    utils.print_list(rbds, columns)

@utils.service_type('vsm')
def do_rbd_pool_summary(cs, args):
    """\033[1;32;40mGets summary info of rbd pool.\033[0m"""
    info = cs.rbd_pools.summary()
    info = info._info
    utils.print_dict(info)


###################server##########################
@utils.arg('server',
           metavar='<server>',
           help='Name or ID of server.')
@utils.service_type('vsm')
def do_server_show(cs, args):
    """\033[1;32;40mShows details info of server.\033[0m"""
    info = dict()
    server = utils.find_server(cs, args.server)
    info.update(server._info)
    utils.print_dict(info)

@utils.service_type('vsm')
def do_server_list(cs, args):
    """\033[1;32;40mLists all servers.\033[0m"""
    result = cs.servers.list()
    columns = ["ID", "HOST", "Type", "Zone ID", "Service ID",
               "Cluster IP", "Secondary Public IP", "Primary Public IP",
               "Raw IP", "Ceph Ver", "OSDs", "Status"]
    utils.print_list(result, columns)

@utils.service_type('vsm')
def do_server_add(cs, args):
    """Adds a new server."""
    _is_developing("server-add",
                   "Adds a new server.")

@utils.arg('--id',
           metavar='<id>',
           action='append',
           default=[],
           help='ID of server.')
@utils.service_type('vsm')
def do_server_remove(cs, args):
    """\033[1;32;40mRemoves a server.\033[0m"""
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
    """\033[1;32;40mStarts a server.\033[0m"""
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
    """\033[1;32;40mStops a server.\033[0m"""
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
@utils.service_type('vsm')
def do_storage_group_create(cs, args):
    """Creates storage group."""
    _is_developing("storage-group-create",
                   "Creates storage group.")

@utils.service_type('vsm')
def do_storage_group_show(cs, args):
    """Shows detail info of storage group."""
    _is_developing("storage-group-show",
                   "Shows detail info of storage group.")

@utils.service_type('vsm')
def do_storage_group_list(cs, args):
    """Lists all storage groups."""
    _is_developing("storage-group-list",
                   "Lists all storage groups.")

@utils.service_type('vsm')
def do_storage_group_summary(cs, args):
    """Gets summary info of storage group."""
    _is_developing("storage-group-summary",
                   "Gets summary info of storage group.")


###################storage pool##########################
@utils.service_type('vsm')
def do_storage_pool_show(cs, args):
    """Shows details info of storage pool."""
    _is_developing("storage-pool-show",
                   "Shows details info of storage pool.")

@utils.service_type('vsm')
def do_storage_pool_list(cs, args):
    """Lists all storage pools."""
    _is_developing("storage-pool-list",
                   "Lists all storage pools.")

@utils.service_type('vsm')
def do_storage_pool_add_cache_tier(cs, args):
    """Adds cache tier pool."""
    _is_developing("storage-pool-add-cache-tier",
                   "Adds cache tier pool.")

@utils.service_type('vsm')
def do_storage_pool_remove_cache_tier(cs, args):
    """Removes cache tier pool."""
    _is_developing("storage-pool-remove-cache-tier",
                   "Removes cache tier pool.")

@utils.service_type('vsm')
def do_storage_pool_restart(cs, args):
    """Restarts storage pool."""
    _is_developing("storage-pool-restart",
                   "Restarts storage pool.")

@utils.service_type('vsm')
def do_storage_pool_delete(cs, args):
    """Deletes storage pool."""
    _is_developing("storage-pool-delete",
                   "Deletes storage pool.")

@utils.service_type('vsm')
def do_storage_pool_list_ec_profiles(cs, args):
    """Lists ec profiles."""
    _is_developing("storage-pool-list-ec-profiles",
                   "Lists ec profiles.")


###################setting##########################
@utils.service_type('vsm')
def do_setting_show(cs, args):
    """Shows details info of setting."""
    _is_developing("setting-show",
                   "Shows details info of setting.")

@utils.service_type('vsm')
def do_setting_list(cs, args):
    """Lists all settings."""
    _is_developing("setting-list",
                   "Lists all settings.")

@utils.service_type('vsm')
def do_setting_create(cs, args):
    """Creates a setting."""
    _is_developing("setting-create",
                   "Creates a setting.")


###################zone##########################
@utils.service_type('vsm')
def do_zone_list(cs, args):
    """Lists all zones."""
    _is_developing("zone-list",
                   "Lists all zones.")


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