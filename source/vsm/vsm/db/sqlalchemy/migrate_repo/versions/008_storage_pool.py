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

from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy import Integer, MetaData, String, Table
from vsm.db.sqlalchemy import models

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine;
    # bind migrate_engine to your metadata
    meta = MetaData()
    meta.bind = migrate_engine

    storage_pools = Table(
        'storage_pools', meta,
        Column('id', Integer, primary_key=True, nullable=False),
        Column('pool_id', Integer, nullable=True),
        Column('name', String(length=255), nullable=False),
        Column('status', String(length=255), default="pending"),
        Column('recipe_id', Integer),
        Column('pg_num', Integer),
        Column('pgp_num', Integer),
        Column('size', Integer),
        Column('min_size', Integer),
        Column('crush_ruleset', Integer, ForeignKey(models.StorageGroup.rule_id, onupdate="CASCADE", ondelete="CASCADE")),
        Column('crash_replay_interval', Integer, nullable=True),
        Column('cluster_id', Integer, ForeignKey(models.Cluster.id), nullable=False),
        Column('created_by', String(length=50), nullable=False),
        Column('tag', String(length=16), nullable=False),
        Column('num_bytes', Integer),
        Column('num_objects', Integer),
        Column('num_object_clones', Integer),
        Column('num_objects_degraded', Integer),
        Column('num_objects_unfound', Integer),
        Column('num_read', Integer),
        Column('num_read_kb', Integer),
        Column('num_write', Integer),
        Column('num_write_kb', Integer),
        Column('read_bytes_sec', Integer),
        Column('write_bytes_sec', Integer),
        Column('op_per_sec', Integer),
        Column('created_at', DateTime(timezone=False)),
        Column('updated_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('deleted', Boolean(create_constraint=True, name=None)),
    )

    try:
        storage_pools.create()
    except Exception:
        meta.drop_all(tables=[storage_pools])
        raise

def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    storage_pools = Table('storage_pools',
                    meta,
                    autoload=True)
    storage_pools.drop()
