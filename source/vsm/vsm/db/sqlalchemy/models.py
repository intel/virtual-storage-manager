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
SQLAlchemy models for vsm data.
"""

from sqlalchemy import Column, Integer
from sqlalchemy import BigInteger, String
from sqlalchemy import Text
from sqlalchemy import Float
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, backref, object_mapper

from vsm.db.sqlalchemy.session import get_session

from vsm import exception
from vsm import flags
from vsm.openstack.common import timeutils

from vsm.openstack.common import log as logging
LOG = logging.getLogger(__name__)

FLAGS = flags.FLAGS
BASE = declarative_base()

class VsmBase(object):
    """Base class for Vsm Models."""
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __table_initialized__ = False
    created_at = Column(DateTime, default=timeutils.utcnow)
    updated_at = Column(DateTime, onupdate=timeutils.utcnow)
    deleted_at = Column(DateTime)
    deleted = Column(Boolean, default=False)
    metadata = None

    def __init__(self):
        self._i = None

    def save(self, session=None):
        """Save this object."""
        if not session:
            session = get_session()
        session.add(self)
        try:
            session.flush()
        except IntegrityError, e:
            if str(e).endswith('is not unique'):
                raise exception.Duplicate(str(e))
            else:
                raise

    def delete(self, session=None):
        """Delete this object."""
        self.deleted = True
        self.deleted_at = timeutils.utcnow()
        self.save(session=session)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __iter__(self):
        self._i = iter(object_mapper(self).columns)
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in values.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        """Make the model object behave like a dict.

        Includes attributes from joins."""
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                      if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()

class Service(BASE, VsmBase):
    """Represents a running service on a host."""

    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    host = Column(String(255))  # , ForeignKey('hosts.id'))
    binary = Column(String(255))
    topic = Column(String(255))
    report_count = Column(Integer, nullable=False, default=0)
    disabled = Column(Boolean, default=False)
    availability_zone = Column(String(255), default='vsm')

class VsmNode(BASE, VsmBase):
    """Represents a running vsm service on a host."""

    __tablename__ = 'vsm_nodes'
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=True)

class Hardware(BASE, VsmBase):
    """Represents a block storage device that can be attached to a vm."""
    __tablename__ = 'storages'
    id = Column(String(36), primary_key=True)

    @property
    def name(self):
        return FLAGS.storage_name_template % self.id

    ec2_id = Column(Integer)
    user_id = Column(String(255))
    project_id = Column(String(255))

    snapshot_id = Column(String(36))

    host = Column(String(255))  # , ForeignKey('hosts.id'))
    size = Column(Integer, default=0)
    availability_zone = Column(String(255))  # TODO(vish): foreign key?
    instance_uuid = Column(String(36))
    mountpoint = Column(String(255))
    attach_time = Column(String(255))  # TODO(vish): datetime
    status = Column(String(255))  # TODO(vish): enum?
    attach_status = Column(String(255))  # TODO(vish): enum

    scheduled_at = Column(DateTime)
    launched_at = Column(DateTime)
    terminated_at = Column(DateTime)

    display_name = Column(String(255))
    display_description = Column(String(255))

    provider_location = Column(String(255))
    provider_auth = Column(String(255))

    storage_type_id = Column(String(36))
    source_volid = Column(String(36))

class HardwareMetadata(BASE, VsmBase):
    """Represents a metadata key/value pair for a storage."""
    __tablename__ = 'storage_metadata'
    id = Column(Integer, primary_key=True)
    key = Column(String(255))
    value = Column(String(255))
    storage_id = Column(String(36), ForeignKey('storages.id'), nullable=False)
    storage = relationship(Hardware, backref="storage_metadata",
                          foreign_keys=storage_id,
                          primaryjoin='and_('
                          'HardwareMetadata.storage_id == Hardware.id,'
                          'HardwareMetadata.deleted == False)')

class HardwareTypes(BASE, VsmBase):
    """Represent possible storage_types of storages offered."""
    __tablename__ = "storage_types"
    id = Column(String(36), primary_key=True)
    name = Column(String(255))

    storages = relationship(Hardware,
                           backref=backref('storage_type', uselist=False),
                           foreign_keys=id,
                           primaryjoin='and_('
                           'Hardware.storage_type_id == HardwareTypes.id, '
                           'HardwareTypes.deleted == False)')

class HardwareTypeExtraSpecs(BASE, VsmBase):
    """Represents additional specs as key/value pairs for a storage_type."""
    __tablename__ = 'storage_type_extra_specs'
    id = Column(Integer, primary_key=True)
    key = Column(String(255))
    value = Column(String(255))
    storage_type_id = Column(String(36),
                            ForeignKey('storage_types.id'),
                            nullable=False)
    storage_type = relationship(
        HardwareTypes,
        backref="extra_specs",
        foreign_keys=storage_type_id,
        primaryjoin='and_('
        'HardwareTypeExtraSpecs.storage_type_id == HardwareTypes.id,'
        'HardwareTypeExtraSpecs.deleted == False)'
    )

class HardwareGlanceMetadata(BASE, VsmBase):
    """Glance metadata for a bootable storage."""
    __tablename__ = 'storage_glance_metadata'
    id = Column(Integer, primary_key=True, nullable=False)
    storage_id = Column(String(36), ForeignKey('storages.id'))
    snapshot_id = Column(String(36), ForeignKey('snapshots.id'))
    key = Column(String(255))
    value = Column(Text)
    storage = relationship(Hardware, backref="storage_glance_metadata",
                          foreign_keys=storage_id,
                          primaryjoin='and_('
                          'HardwareGlanceMetadata.storage_id == Hardware.id,'
                          'HardwareGlanceMetadata.deleted == False)')

class Quota(BASE, VsmBase):
    """Represents a single quota override for a project.

    If there is no row for a given project id and resource, then the
    default for the quota class is used.  If there is no row for a
    given quota class and resource, then the default for the
    deployment is used. If the row is present but the hard limit is
    Null, then the resource is unlimited.
    """

    __tablename__ = 'quotas'
    id = Column(Integer, primary_key=True)

    project_id = Column(String(255), index=True)

    resource = Column(String(255))
    hard_limit = Column(Integer, nullable=True)

class QuotaClass(BASE, VsmBase):
    """Represents a single quota override for a quota class.

    If there is no row for a given quota class and resource, then the
    default for the deployment is used.  If the row is present but the
    hard limit is Null, then the resource is unlimited.
    """

    __tablename__ = 'quota_classes'
    id = Column(Integer, primary_key=True)

    class_name = Column(String(255), index=True)

    resource = Column(String(255))
    hard_limit = Column(Integer, nullable=True)

class QuotaUsage(BASE, VsmBase):
    """Represents the current usage for a given resource."""

    __tablename__ = 'quota_usages'
    id = Column(Integer, primary_key=True)

    project_id = Column(String(255), index=True)
    resource = Column(String(255))

    in_use = Column(Integer)
    reserved = Column(Integer)

    @property
    def total(self):
        return self.in_use + self.reserved

    until_refresh = Column(Integer, nullable=True)

class Reservation(BASE, VsmBase):
    """Represents a resource reservation for quotas."""

    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False)

    usage_id = Column(Integer, ForeignKey('quota_usages.id'), nullable=False)

    project_id = Column(String(255), index=True)
    resource = Column(String(255))

    delta = Column(Integer)
    expire = Column(DateTime, nullable=False)

class Migration(BASE, VsmBase):
    """Represents a running host-to-host migration."""
    __tablename__ = 'migrations'
    id = Column(Integer, primary_key=True, nullable=False)
    # NOTE(tr3buchet): the ____compute variables are instance['host']
    source_compute = Column(String(255))
    dest_compute = Column(String(255))
    # NOTE(tr3buchet): dest_host, btw, is an ip address
    dest_host = Column(String(255))
    old_instance_type_id = Column(Integer())
    new_instance_type_id = Column(Integer())
    instance_uuid = Column(String(255),
                           ForeignKey('instances.uuid'),
                           nullable=True)
    #TODO(_cerberus_): enum
    status = Column(String(255))

class SMFlavors(BASE, VsmBase):
    """Represents a flavor for SM storages."""
    __tablename__ = 'sm_flavors'
    id = Column(Integer(), primary_key=True)
    label = Column(String(255))
    description = Column(String(255))

class SMBackendConf(BASE, VsmBase):
    """Represents the connection to the backend for SM."""
    __tablename__ = 'sm_backend_config'
    id = Column(Integer(), primary_key=True)
    flavor_id = Column(Integer, ForeignKey('sm_flavors.id'), nullable=False)
    sr_uuid = Column(String(255))
    sr_type = Column(String(255))
    config_params = Column(String(2047))

class SMHardware(BASE, VsmBase):
    __tablename__ = 'sm_storage'
    id = Column(String(36), ForeignKey(Hardware.id), primary_key=True)
    backend_id = Column(Integer, ForeignKey('sm_backend_config.id'),
                        nullable=False)
    vdi_uuid = Column(String(255))

class Backup(BASE, VsmBase):
    """Represents a backup of a storage to Swift."""
    __tablename__ = 'backups'
    id = Column(String(36), primary_key=True)

    @property
    def name(self):
        return FLAGS.backup_name_template % self.id

    user_id = Column(String(255), nullable=False)
    project_id = Column(String(255), nullable=False)

    storage_id = Column(String(36), nullable=False)
    host = Column(String(255))
    availability_zone = Column(String(255))
    display_name = Column(String(255))
    display_description = Column(String(255))
    container = Column(String(255))
    status = Column(String(255))
    fail_reason = Column(String(255))
    service_metadata = Column(String(255))
    service = Column(String(255))
    size = Column(Integer, default=0)
    object_count = Column(Integer)

def register_models():
    """Register Models and create metadata.

    Called from vsm.db.sqlalchemy.__init__ as part of loading the driver,
    it will never need to be called explicitly elsewhere unless the
    connection is lost and needs to be reestablished.
    """
    from sqlalchemy import create_engine
    models = (Backup,
              Migration,
              Service,
              SMBackendConf,
              SMFlavors,
              SMHardware,
              Hardware,
              HardwareMetadata,
              HardwareTypeExtraSpecs,
              HardwareTypes,
              HardwareGlanceMetadata,
              )
    engine = create_engine(FLAGS.sql_connection, echo=False)
    for model in models:
        model.metadata.create_all(engine)

class ComputeNode(BASE, VsmBase):
    """Represents a running compute service on a host."""

    __tablename__ = 'compute_nodes'
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=True)
    service = relationship(Service,
                           backref=backref('compute_node'),
                           foreign_keys=service_id,
                           primaryjoin='and_('
                                'ComputeNode.service_id == Service.id,'
                                'ComputeNode.deleted == False)')

    vcpus = Column(Integer)
    memory_mb = Column(Integer)
    local_gb = Column(Integer)
    vcpus_used = Column(Integer)
    memory_mb_used = Column(Integer)
    local_gb_used = Column(Integer)

    # Free Ram, amount of activity (resize, migration, boot, etc) and
    # the number of running VM's are a good starting point for what's
    # important when making scheduling decisions.
    #
    # NOTE(sandy): We'll need to make this extensible for other schedulers.
    free_ram_mb = Column(Integer)
    free_disk_gb = Column(Integer)
    current_workload = Column(Integer)

    # Note(masumotok): Expected Strings example:
    #
    # '{"arch":"x86_64",
    #   "model":"Nehalem",
    #   "topology":{"sockets":1, "threads":2, "cores":3},
    #   "features":["tdtscp", "xtpr"]}'
    #
    # Points are "json translatable" and it must have all dictionary keys
    # above, since it is copied from <cpu> tag of getCapabilities()
    # (See libvirt.virtConnection).
    cpu_info = Column(Text, nullable=True)
    disk_available_least = Column(Integer)
    cpu_utilization = Column(Float(), default=0.0)
    #cluster_id = Column(Integer), nullable=True)

class Device(BASE, VsmBase):
    """This table store the information about device on host"""

    __tablename__ = 'devices'
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    service = relationship(Service,
                           backref=backref('device'),
                           foreign_keys=service_id,
                           primaryjoin='and_('
                           'Device.service_id == Service.id,'
                           'Device.deleted == False)')

    name = Column(String(length=255), nullable=False)
    path = Column(String(length=255), nullable=False)
    journal = Column(String(length=255), nullable=True)
    #total_capacity_gb = Column(Float(), nullable=False)
    #free_capacity_gb = Column(Float())
    total_capacity_kb = Column(BigInteger, default=0, nullable=False)
    used_capacity_kb = Column(BigInteger, default=0, nullable=False)
    avail_capacity_kb = Column(BigInteger, default=0, nullable=False)
    device_type = Column(String(length=255))
    interface_type = Column(String(length=255))
    fs_type = Column(String(length=255), default="xfs")
    mount_point = Column(String(length=255))
    state = Column(String(length=255), default="MISSING")
    journal_state = Column(String(length=255), default="MISSING")

class StorageGroup(BASE, VsmBase):
    """This table store the storage groups"""

    __tablename__ = 'storage_groups'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    storage_class = Column(String(length=255), nullable=False)
    friendly_name = Column(String(length=255), nullable=False)
    rule_id = Column(Integer, nullable=False)
    drive_extended_threshold = Column(Integer, default=0, nullable=False)
    status = Column(String(length=255), default="OUT", nullable=False)

class Zone(BASE, VsmBase):
    """This table store the zones"""

    __tablename__ = 'zones'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)

class OsdState(BASE, VsmBase):
    """This table maintains the information about osd."""

    __tablename__ = 'osd_states'
    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    service = relationship(Service,
                           backref=backref('osd_state'),
                           foreign_keys=service_id,
                           primaryjoin='and_('
                           'OsdState.service_id == Service.id,'
                           'OsdState.deleted == False)')
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=False)
    zone = relationship(Zone,
                            backref=backref('osd_state'),
                            foreign_keys=zone_id,
                            primaryjoin='and_('
                                'OsdState.zone_id== Zone.id,'
                                'OsdState.deleted == False)')
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    device = relationship(Device,
                          backref=backref('osd_state'),
                          foreign_keys=device_id,
                          primaryjoin='and_('
                          'OsdState.device_id == Device.id,'
                          'OsdState.deleted == False)')
    storage_group_id = Column(Integer,
                              ForeignKey('storage_groups.id'),
                              nullable=False)
    storage_group = relationship(StorageGroup,
                                 backref=backref('osd_state'),
                                 foreign_keys=storage_group_id,
                                 primaryjoin='and_('
                                 'OsdState.storage_group_id == StorageGroup.id,'
                                 'OsdState.deleted == False)')

    osd_name = Column(String(length=255), unique=True, nullable=False)
    cluster_id = Column(Integer)
    state = Column(String(length=255), default="down")
    public_ip = Column(String(length=255))
    cluster_ip = Column(String(length=255))
    weight = Column(Float)
    operation_status = Column(String(length=255))

class CrushMap(BASE, VsmBase):
    """The table mainly store the content of crush map which encoded as text."""

    __tablename__ = 'crushmaps'
    id = Column(Integer, primary_key=True, nullable=False)
    content = Column(Text, nullable=True)

class Recipe(BASE, VsmBase):
    """This table store the recipes."""

    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True, nullable=False)
    recipe_name = Column(String(length=255), unique=True, nullable=False)
    pg_num = Column(Integer, nullable=False)
    pgp_num = Column(Integer, nullable=False)
    size = Column(Integer, default=0, nullable=False)
    min_size = Column(Integer)
    crush_ruleset = Column(Integer, nullable=False)
    crash_replay_interval = Column(Integer)

class VsmCapacityManage(BASE, VsmBase):
    """ VSM user capacity management

    To manage the capacity that VSM user can use. The most important in
    this table is capacity_quota_mb and capacity_used_mb which denote
    the quota storage and used storage respectively.
    """

    __tablename__ = 'vsm_capacity_manages'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    capacity_quota_mb = Column(Integer)
    capacity_used_mb = Column(Integer)
    testyr = Column(Integer)

class Cluster(BASE, VsmBase):
    """This table store the clusters."""

    __tablename__ = 'clusters'
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=True)
    file_system = Column(String(length=255), default='xfs', nullable=True)
    primary_public_network = Column(String(length=255), nullable=True)
    secondary_public_network = Column(String(length=255), nullable=True)
    cluster_network = Column(String(length=255), nullable=True)
    journal_size = Column(Integer, default=0)
    deleted_times = Column(Integer, default=0)
    info_dict = Column(Text, nullable=True)
    ceph_conf = Column(String(length=10485760), nullable=True)

class StoragePool(BASE, VsmBase):
    """This table store the storage pools."""

    __tablename__ = 'storage_pools'
    id = Column(Integer, primary_key=True, nullable=False)
    pool_id = Column(Integer, nullable=False)
    name = Column(String(length=255), nullable=False)
    status = Column(String(length=255), default="pending")
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    recipes = relationship(Recipe,
                            backref=backref('storage_pool'),
                            foreign_keys=recipe_id,
                            primaryjoin='and_('
                                'StoragePool.recipe_id == Recipe.id,'
                                'StoragePool.deleted == False)')
    cluster_id = Column(Integer, ForeignKey('clusters.id'), nullable=False)
    cluster = relationship(Cluster,
                           backref=backref('storage_pool'),
                           foreign_keys=cluster_id,
                           primaryjoin='and_('
                           'StoragePool.cluster_id == Cluster.id,'
                           'StoragePool.deleted == False)')
    pg_num = Column(Integer)
    pgp_num = Column(Integer)
    size = Column(Integer, default=0)
    min_size = Column(Integer)
    #TODO this crush_ruleset is diff from the rule_id in storage groups
    #crush_ruleset = Column(Integer, ForeignKey('storage_groups.rule_id'), nullable=False)
    #ruleset = relationship(StorageGroup,
    #                       backref=backref('storage_pool'),
    #                       foreign_keys=crush_ruleset,
    #                       primaryjoin='and_('
    #                       'StoragePool.crush_ruleset == StorageGroup.rule_id,'
    #                       'StoragePool.deleted == False)')
    crush_ruleset = Column(Integer, nullable=False)  
    primary_storage_group_id = Column(Integer, ForeignKey('storage_groups.id'), nullable=False)
    storage_group = relationship(StorageGroup,
                           backref=backref('storage_pool'),
                           foreign_keys=primary_storage_group_id,
                           primaryjoin='and_('
                           'StoragePool.primary_storage_group_id == StorageGroup.id,'
                           'StoragePool.deleted == False)')
    crash_replay_interval = Column(Integer)
    created_by = Column(String(length=50), nullable=False)
    tag = Column(String(length=16), nullable=False)
    num_bytes = Column(Integer)
    num_objects = Column(Integer)
    num_object_clones = Column(Integer)
    num_objects_degraded = Column(Integer)
    num_objects_unfound = Column(Integer)
    num_read = Column(Integer)
    num_read_kb = Column(Integer)
    num_write = Column(Integer)
    num_write_kb = Column(Integer)
    read_bytes_sec = Column(Integer)
    write_bytes_sec = Column(Integer)
    op_per_sec = Column(Integer)
    ec_status = Column(String(length=255))
    cache_tier_status = Column(String(length=255))
    quota = Column(Integer, default=None)
    cache_mode = Column(String(length=255))
    replica_storage_group =Column(String(length=255))

class InitNode(BASE, VsmBase):
    """This table init nodes."""

    __tablename__ = 'init_nodes'
    id = Column(Integer, primary_key=True, nullable=False)
    host = Column(String(length=255), nullable=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    service = relationship(Service,
                            backref=backref('init_node'),
                            foreign_keys=service_id,
                            primaryjoin='and_('
                                'InitNode.service_id == Service.id,'
                                'InitNode.deleted == False)')
    raw_ip = Column(String(length=255), nullable=True)
    primary_public_ip = Column(String(length=255), nullable=True)
    secondary_public_ip = Column(String(length=255), nullable=True)
    cluster_ip = Column(String(length=255), nullable=True)
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=True)
    zone = relationship(Zone,
                            backref=backref('init_node'),
                            foreign_keys=zone_id,
                            primaryjoin='and_('
                                'InitNode.zone_id== Zone.id,'
                                'InitNode.deleted == False)')

    mds = Column(String(length=255), nullable=True)
    type = Column(String(length=255), nullable=True)
    id_rsa_pub = Column(String(length=1024), nullable=True)

    cluster_id = Column(Integer,
                        ForeignKey('clusters.id'),
                        nullable=False)
    cluster = relationship(Cluster,
                            backref=backref('init_node'),
                            foreign_keys=cluster_id,
                            primaryjoin='and_('
                                'InitNode.cluster_id == Cluster.id,'
                                'InitNode.deleted == False)')
    data_drives_number = Column(String(length=255), nullable=True)
    status = Column(String(length=255), default='not available', nullable=True)
    pre_status = Column(String(length=255), nullable=True)

    def __repr__(self):
        return 'Host: %s' % self.host

class Vsmapp(BASE, VsmBase):
    """This tables contains the cluster info which will consume ceph."""
    __tablename__ = 'vsmapps'
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    project_id = Column(Integer, nullable=False)
    uuid = Column(String(length=255), nullable=False)
    display_name = Column(String(length=50), nullable=True)
    app_type = Column(String(length=50), default='OpenStack')
    storage_type = Column(String(length=50), default='rbd')
    status = Column(String(length=50), nullable=True)

class Appnode(BASE, VsmBase):
    """This table stores all the appnodes info."""
    __tablename__ = 'appnodes'

    id = Column(Integer, primary_key=True, nullable=False)
    ip = Column(String(length=50), nullable=False)
    vsmapp_id = Column(Integer, ForeignKey(Vsmapp.id), nullable=False)
    ssh_status = Column(String(length=50), nullable=True)
    log_info = Column(Text, nullable=True)
    vsmapp = relationship(Vsmapp,
                          backref=backref('appnode'),
                          foreign_keys=vsmapp_id,
                          primaryjoin='and_('
                          'Appnode.vsmapp_id == Vsmapp.id,'
                          'Appnode.deleted == False)')

class StoragePoolUsage(BASE, VsmBase):
    """Storage pool usage """
    __tablename__ = 'storage_pool_usages'

    id = Column(Integer, primary_key=True, nullable=False)
    pool_id = Column(Integer,
                     ForeignKey(StoragePool.id),
                     nullable=False)
    vsmapp_id = Column(Integer,
                       ForeignKey(Vsmapp.id),
                       nullable=False)
    attach_status = Column(String(length=255), nullable=False)
    pools = relationship(StoragePool,
                         backref=backref('storage_pool_usage'),
                         foreign_keys=pool_id,
                         primaryjoin='and_('
                         'StoragePoolUsage.pool_id == StoragePool.id,'
                         'StoragePoolUsage.deleted == False)')
    attach_at = Column(DateTime, default=timeutils.utcnow)
    terminate_at = Column(DateTime)

    vsmapps = relationship(Vsmapp,
                           backref=backref('storage_pool_usage'),
                           foreign_keys=vsmapp_id,
                           primaryjoin='and_('
                           'StoragePoolUsage.vsmapp_id == Vsmapp.id,'
                           'StoragePoolUsage.deleted == False)')

class Summary(BASE, VsmBase):
    """ ceph summary report """
    __tablename__ = 'summary'

    id = Column(Integer, primary_key=True, nullable=False)
    cluster_id = Column(Integer,
                        ForeignKey('clusters.id'),
                        nullable=False)
    summary_type = Column(String(length=50), nullable=False)
    summary_data = Column(Text, nullable=False)
    cluster = relationship(Cluster,
                           backref=backref('summary'),
                           foreign_keys=cluster_id,
                           primaryjoin='and_('
                                       'Summary.cluster_id == Cluster.id,'
                                       'Summary.deleted == False)')

class Monitor(BASE, VsmBase):
    """ ceph monitor stat data"""
    __tablename__ = 'monitors'

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    address = Column(String(length=255))
    health = Column(String(length=255))
    details = Column(String(length=255))
    skew = Column(String(length=255))
    latency = Column(String(length=255))
    kb_total = Column(Integer)
    kb_used = Column(Integer)
    kb_avail = Column(Integer)
    avail_percent = Column(Integer)

class PlacementGroup(BASE, VsmBase):
    """ ceph placement group report """
    __tablename__ = 'placement_groups'

    id = Column(Integer, primary_key=True, nullable=False)
    pgid = Column(String(length=255), nullable=False)
    state = Column(String(length=255), nullable=False)
    up = Column(String(length=255), nullable=False)
    acting = Column(String(length=255), nullable=False)

class LicenseStatus(BASE, VsmBase):
    """License status """
    __tablename__ = 'license_status'

    id = Column(Integer, primary_key=True)
    license_accept = Column(Boolean, default=False)
    #FIXME(fengqian): Does it need to add user info here?
    #user_name = Column(String(length=50), nullable=False)

class RBD(BASE, VsmBase):
    """ ceph rbd report """
    __tablename__ = 'rbds'

    id = Column(Integer, primary_key=True, nullable=False)
    pool = Column(String(length=255), nullable=False)
    image = Column(String(length=255), nullable=False)
    size = Column(BigInteger, nullable=False)
    format = Column(Integer, nullable=False)
    objects = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)

class MDS(BASE, VsmBase):
    """ ceph MDS report """
    __tablename__ = 'mdses'

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    gid = Column(Integer, nullable=False)
    state = Column(String(length=255), nullable=False)
    address = Column(String(length=255), nullable=False)

class VsmSettings(BASE, VsmBase):
    """ vsm UI settings and vsm settings model
    """
    __tablename__ = 'vsm_settings'

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    value = Column(String(length=255), nullable=False)
    default_value = Column(String(length=255), nullable=False)

class ErasureCodeProfile(BASE, VsmBase):
    """erasure code profile  """
    __tablename__ = 'ec_profiles'

    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(length=255), nullable=False)
    plugin = Column(String(length=255), nullable=False)
    plugin_path = Column(String(length=255), nullable=False)
    pg_num = Column(Integer, nullable=False)
    plugin_kv_pair = Column(Text, nullable=False)
    

class LongCalls(BASE, VsmBase):
    """This table store the long_calls."""

    __tablename__ = 'long_calls'
    id = Column(Integer, primary_key=True, nullable=False)
    uuid = Column(String(length=255), nullable=False)
    status = Column(String(length=255), nullable=False)
