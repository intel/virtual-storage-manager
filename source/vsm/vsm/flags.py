# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright 2012 Red Hat, Inc.
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

"""Command-line flag library.

Emulates gflags by wrapping cfg.ConfigOpts.

The idea is to move fully to cfg eventually, and this wrapper is a
stepping stone.

"""

import os
import socket
import sys

from oslo.config import cfg
from vsm import version

FLAGS = cfg.CONF

def parse_args(argv, default_config_files=None):
    FLAGS(argv[1:], project='vsm',
          version=version.version_string(),
          default_config_files=default_config_files)

class UnrecognizedFlag(Exception):
    pass

def DECLARE(name, module_string, flag_values=FLAGS):
    if module_string not in sys.modules:
        __import__(module_string, globals(), locals())
    if name not in flag_values:
        raise UnrecognizedFlag('%s not defined by %s' % (name, module_string))

def _get_my_ip():
    """
    Returns the actual ip of the local machine.

    This code figures out what source address would be used if some traffic
    were to be sent out to some well known address on the Internet. In this
    case, a Google DNS server is used, but the specific address does not
    matter much.  No traffic is actually sent.
    """
    try:
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('8.8.8.8', 80))
        (addr, port) = csock.getsockname()
        csock.close()
        return addr
    except socket.error:
        return "127.0.0.1"

core_opts = [
    cfg.StrOpt('connection_type',
               default=None,
               help='Virtualization api connection type : libvirt, xenapi, '
                    'or fake'),
    cfg.StrOpt('sql_connection',
               default='sqlite:///$state_path/$sqlite_db',
               help='The SQLAlchemy connection string used to connect to the '
                    'database',
               secret=True),
    cfg.IntOpt('sql_connection_debug',
               default=0,
               help='Verbosity of SQL debugging information. 0=None, '
                    '100=Everything'),
    cfg.StrOpt('api_paste_config',
               default="api-paste.ini",
               help='File name for the paste.deploy config for vsm-api'),
    cfg.StrOpt('pybasedir',
               default=os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                    '../')),
               help='Directory where the vsm python module is installed'),
    cfg.StrOpt('bindir',
               default='$pybasedir/bin',
               help='Directory where vsm binaries are installed'),
    cfg.StrOpt('state_path',
               default='$pybasedir',
               help="Top-level directory for maintaining vsm's state"), ]

debug_opts = [
]

tests_opts = [
    cfg.StrOpt('testdb_manager',
               default='vsm.tests.db.manager.TestDBManager',
               help='full class name for the Manager for storage backup'),
    cfg.StrOpt('testdb_topic',
               default='vsm-testdb',
               help='the topic testdb nodes listen on'),
]

FLAGS.register_cli_opts(core_opts)
FLAGS.register_cli_opts(debug_opts)
FLAGS.register_cli_opts(tests_opts)

global_opts = [
    cfg.StrOpt('bypath_dir',
               default='/dev/disk/by-path/',
               help='by-path dir'),
    cfg.StrOpt('cluster_manifest',
               default='/etc/manifest/cluster.manifest',
               help='cluster.manifest'),
    cfg.StrOpt('vsm_config',
               default='/etc/vsm/vsm.conf',
               help='vsm.conf'),
    cfg.StrOpt('crushmap_bin',
               default='/etc/vsm/crushmap.bin',
               help='crushmap.bin'),
    cfg.StrOpt('crushmap_src',
               default='/etc/vsm/crushmap.src',
               help='crushmap.src'),
    cfg.StrOpt('default_weight',
               default=0.1,
               help='default weight of empty item'),
    cfg.StrOpt('ceph_conf_template',
               default='/etc/vsm/ceph.conf.template',
               help='Default template of ceph.conf'),
    cfg.StrOpt('mon_keyring',
               default='/etc/ceph/ceph.mon.keyring',
               help='Key ring localtion.'),
    cfg.StrOpt('vsm_user',
               default='vsm',
               help='user name of vsm'),
    cfg.StrOpt('my_ip',
               default=_get_my_ip(),
               help='ip address of this host'),
    cfg.StrOpt('glance_host',
               default='$my_ip',
               help='default glance hostname or ip'),
    cfg.IntOpt('glance_port',
               default=9292,
               help='default glance port'),
    cfg.ListOpt('glance_api_servers',
                default=['$glance_host:$glance_port'],
                help='A list of the glance api servers available to vsm '
                     '([hostname|ip]:port)'),
    cfg.IntOpt('glance_api_version',
               default=1,
               help='Version of the glance api to use'),
    cfg.IntOpt('glance_num_retries',
               default=0,
               help='Number retries when downloading an image from glance'),
    cfg.BoolOpt('glance_api_insecure',
                default=False,
                help='Allow to perform insecure SSL (https) requests to '
                'glance'),
    cfg.StrOpt('agent_topic',
               default='vsm-agent',
               help='the topic agent nodes listen on'),
    cfg.StrOpt('ml_topic',
               default='vsm-ml',
               help='the topic ML nodes listen on'),
    cfg.StrOpt('conductor_topic',
               default='vsm-conductor',
               help='the topic conductor nodes listen on'),
    cfg.StrOpt('physical_topic',
               default='vsm-physical',
               help='the topic physical nodes listen on'),
    cfg.StrOpt('operation_topic',
               default='vsm-operation',
               help='the topic operation nodes listen on'),
    cfg.StrOpt('scheduler_topic',
               default='vsm-scheduler',
               help='the topic scheduler nodes listen on'),
    cfg.StrOpt('publisher_topic',
               default='vsm-publisher',
               help='the topic publisher nodes listen on'),
    cfg.StrOpt('storage_topic',
               default='vsm-storage',
               help='the topic storage nodes listen on'),
    cfg.StrOpt('backup_topic',
               default='vsm-backup',
               help='the topic storage backup nodes listen on'),
    cfg.BoolOpt('enable_v1_api',
                default=True,
                help=_("Deploy v1 of the Vsm API. ")),
    cfg.BoolOpt('enable_v2_api',
                default=True,
                help=_("Deploy v2 of the Vsm API. ")),
    cfg.BoolOpt('api_rate_limit',
                default=True,
                help='whether to rate limit the api'),
    cfg.ListOpt('vsmapi_storage_ext_list',
                default=[],
                help='Specify list of extensions to load when using osapi_'
                     'storage_extension option with vsm.api.contrib.'
                     'select_extensions'),
    cfg.MultiStrOpt('vsmapi_storage_extension',
                    default=['vsm.api.contrib.standard_extensions'],
                    help='osapi storage extension to load'),
    cfg.StrOpt('vsmapi_storage_base_URL',
               default=None,
               help='Base URL that will be presented to users in links '
                    'to the OpenStack Hardware API',
               deprecated_name='osapi_compute_link_prefix'),
    cfg.IntOpt('osapi_max_limit',
               default=1000,
               help='the maximum number of items returned in a single '
                    'response from a collection resource'),
    cfg.StrOpt('sqlite_db',
               default='vsm.sqlite',
               help='the filename to use with sqlite'),
    cfg.BoolOpt('sqlite_synchronous',
                default=True,
                help='If passed, use synchronous mode for sqlite'),
    cfg.IntOpt('sql_idle_timeout',
               default=3600,
               help='timeout before idle sql connections are reaped'),
    cfg.IntOpt('sql_max_retries',
               default=10,
               help='maximum db connection retries during startup. '
                    '(setting -1 implies an infinite retry count)'),
    cfg.IntOpt('sql_retry_interval',
               default=10,
               help='interval between retries of opening a sql connection'),
    cfg.StrOpt('backup_manager',
               default='vsm.backup.manager.BackupManager',
               help='full class name for the Manager for storage backup'),
    cfg.StrOpt('conductor_manager',
               default='vsm.conductor.manager.ConductorManager',
               help='full class name for the Manager for Conductor'),
    cfg.StrOpt('physical_manager',
               default='vsm.physical.manager.PhysicalManager',
               help='full class name for the Manager for Physical'),
    cfg.StrOpt('ntp_keys',
               default='/etc/ntp/ntp.keys',
               help='ntp sync time key'),
    cfg.StrOpt('ssh_key_gen_shell',
               default='/usr/bin/key',
               help='ssh key gen shell'),
    cfg.StrOpt('id_rsa_pub',
               default='/root/.ssh/id_rsa.pub',
               help='id_rsa.pub'),
    cfg.StrOpt('key_name',
               default='/root/.ssh/id_rsa',
               help='the name of key'),
    #TODO change /root/ path.
    cfg.StrOpt('ssh_authorized_keys',
               default='/root/.ssh/authorized_keys',
               help='ssh key gen shell'),
    cfg.StrOpt('ssh_config',
               default='/etc/ssh/ssh_config',
               help='ssh config file path in ~/.ssh'),
    cfg.StrOpt('etc_hosts',
               default='/etc/hosts',
               help='host name list'),
    #TODO should we rerange the flags.py file?
    #such as ceph in a group.
    #Manager in a group.
    cfg.StrOpt('ceph_conf',
               default='/etc/ceph/ceph.conf',
               help='ceph config file path.'),
    cfg.StrOpt('keyring_admin',
               default='/etc/ceph/keyring.admin',
               help='key ring file path.'),
    cfg.StrOpt('monitor_data_path',
               default='/var/lib/ceph/mon/',
               help='Monitor data path to store information.'),
    cfg.StrOpt('osd_data_path',
               default='/var/lib/ceph/osd/',
               help='OSD data path to store information.'),
    cfg.StrOpt('agent_manager',
               default='vsm.agent.manager.AgentManager',
               help='full class name for the Manager for Conductor'),
    cfg.StrOpt('sockclient_port',
               default=8002,
               help='default port of sockclient'),
    cfg.StrOpt('server_manifest',
               default='/etc/manifest/server.manifest',
               help='default path of server.manifest'),
    cfg.IntOpt('ceph_connect_timeout',
               default=100,
               help='The default ceph connect timeout value.'),
    #cfg.StrOpt('id_rsa_pub',
    #           default='/root/.ssh/id_rsa.pub',
    #           help='path of id_rsa.pub'),
    cfg.StrOpt('vsm_config_path',
               default='/etc/vsm/',
               help='configure path of vsm to reside vsm.conf api-paste.ini'),
    cfg.StrOpt('sockclient_manager',
               default='vsm.sockclient.manager.SockClientManager',
               help='full class name for the Manager for Sockclient'),
    cfg.StrOpt('scheduler_manager',
               default='vsm.scheduler.manager.SchedulerManager',
               help='full class name for the Manager for Scheduler'),
    cfg.StrOpt('host',
               default=socket.gethostname(),
               help='Name of this node.  This can be an opaque identifier.  '
                    'It is not necessarily a hostname, FQDN, or IP address.'),
    # NOTE(vish): default to nova for compatibility with nova installs
    cfg.StrOpt('storage_availability_zone',
               default='nova',
               help='availability zone of this node'),
    cfg.ListOpt('memcached_servers',
                default=None,
                help='Memcached servers or None for in process cache.'),
    cfg.StrOpt('default_storage_type',
               default=None,
               help='default storage type to use'),
    cfg.StrOpt('storage_usage_audit_period',
               default='month',
               help='time period to generate storage usages for.  '
                    'Time period must be hour, day, month or year'),
    cfg.StrOpt('root_helper',
               default='sudo',
               help='Deprecated: command to use for running commands as root'),
    cfg.StrOpt('rootwrap_config',
               default=None,
               help='Path to the rootwrap configuration file to use for '
                    'running commands as root'),
    cfg.BoolOpt('monkey_patch',
                default=False,
                help='Whether to log monkey patching'),
    cfg.ListOpt('monkey_patch_modules',
                default=[],
                help='List of modules/decorators to monkey patch'),
    cfg.IntOpt('service_down_time',
               default=60,
               help='maximum time since last check-in for up service'),
    cfg.IntOpt('server_ping_time',
               default=5,
               help='The interval of time to ping other servers.'),
    cfg.IntOpt('ping_count',
               default=5,
               help='The hop that ping will walk.'),
    cfg.IntOpt('time_out',
               default=400,
               help='The default timeout value.'),
    cfg.IntOpt('update_time_interval',
               default=1,
               help='The interval that each server update its update_at field.'
                    'This value should be three times less than other update'
                    'interval, such as server_ping_time'),
    cfg.StrOpt('storage_api_class',
               default='vsm.storage.api.API',
               help='The full class name of the storage API class to use'),
    cfg.StrOpt('backup_api_class',
               default='vsm.backup.api.API',
               help='The full class name of the storage backup API class'),
    cfg.StrOpt('auth_strategy',
               default='noauth',
               help='The strategy to use for auth. Supports noauth, keystone, '
                    'and deprecated.'),
    cfg.ListOpt('enabled_backends',
                default=None,
                help='A list of backend names to use. These backend names '
                     'should be backed by a unique [CONFIG] group '
                     'with its options'),
    cfg.BoolOpt('no_snapshot_gb_quota',
                default=False,
                help='Whether snapshots count against GigaByte quota'),
    cfg.StrOpt('default_zone',
                default='zone_one',
                help='The default one zone name'), ]

FLAGS.register_opts(global_opts)

db_opts = [
    cfg.BoolOpt('enable_new_services',
                default=True,
                help='Services to be added to the available pool on create'),
]

FLAGS.register_opts(db_opts)

disk_worker_opts = [
    cfg.StrOpt('partition_status_missing',
             default='MISSING',
             help='the partition status is missing'),
    cfg.StrOpt('partition_status_ok',
             default='OK',
             help='the partition status is ok'),
]

FLAGS.register_opts(disk_worker_opts)

osd_opts = [
    cfg.StrOpt('osd_state_autoout',
              default='autoout',
              help='the real osd autoout state'),
    cfg.StrOpt('osd_in_up',
              default='In-Up',
              help='osd in and up status'),
    cfg.StrOpt('osd_in_down',
              default='In-Down',
              help='osd in and down status'),
    cfg.StrOpt('osd_out_up',
              default='Out-Up',
              help='osd out and up status'),
    cfg.StrOpt('osd_out_down',
              default='Out-Down',
              help='osd out and down status'),
    cfg.StrOpt('osd_out_down_autoout',
              default='Out-Down-Autoout',
              help='osd out down autoout status'),
]

FLAGS.register_opts(osd_opts)

storage_group_opts = [
    cfg.StrOpt('storage_group_in',
                default='IN',
                help='IN means the storage group is in Ceph'),
    cfg.StrOpt('storage_group_out',
                default='OUT',
                help='OUT means the storage group is not in Ceph'),

]

FLAGS.register_opts(storage_group_opts)

vsm_status_opts = [
    cfg.StrOpt('vsm_status_removed',
              default='Removed',
              help='removed status'),
    cfg.StrOpt('vsm_status_present',
              default='Present',
              help='prisent status'),
]

FLAGS.register_opts(vsm_status_opts)

summary_type_opts = [
    cfg.StrOpt('summary_type_osd',
              default='osd',
              help='summary type osd'),
    cfg.StrOpt('summary_type_pg',
              default='pg',
              help='summary type pg'),
    cfg.StrOpt('summary_type_mon',
              default='mon',
              help='summary type mon'),
    cfg.StrOpt('summary_type_mds',
              default='mds',
              help='summary type mds'),
    cfg.StrOpt('summary_type_cluster',
              default='cluster',
              help='summary type cluster'),
    cfg.StrOpt('summary_type_vsm',
              default='vsm',
              help='summary type vsm'),
    cfg.StrOpt('summary_type_ceph',
              default='ceph',
              help='summary type ceph'),

]

FLAGS.register_opts(summary_type_opts)

vsm_settings_opts = [
    cfg.IntOpt('storage_group_near_full_threshold',
               default=65,
               help='storage group near full threshold'),
    cfg.IntOpt('storage_group_full_threshold',
               default=85,
               help='storage group full threshold'),
    cfg.IntOpt('ceph_status',
               default=60,
               help='ceph status (secs)'),
    cfg.IntOpt('ceph_osd_pool_stats',
               default=60,
               help='ceph osd pool stats (secs)'),
    cfg.IntOpt('reset_pg_heart_beat',
               default=600,
               help='reset pg_num heart beat(secs)'),
    cfg.IntOpt('ceph_osd_dump',
               default=600,
               help='ceph osd dump (secs)'),
    cfg.IntOpt('ceph_pg_dump_osds',
               default=600,
               help='ceph pg dump osds (secs)'),
    cfg.IntOpt('ceph_osd_tree',
               default=600,
               help='ceph osd tree (secs)'),
    cfg.IntOpt('ceph_pg_dump_pgs_brief',
               default=1800,
               help='ceph pg dump pgs brief (secs)'),
    cfg.IntOpt('rbd_ls_-l_{pool_name}',
               default=1800,
               help='rbd ls -l {pool_name} (secs)'),
    cfg.IntOpt('ceph_mds_dump',
               default=60,
               help='ceph mds dump (secs)'),
]

FLAGS.register_opts(vsm_settings_opts)
