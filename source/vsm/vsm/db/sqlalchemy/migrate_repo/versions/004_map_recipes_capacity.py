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
from sqlalchemy import Table, Text, Float

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine;
    # bind migrate_engine to your metadata
    meta = MetaData()
    meta.bind = migrate_engine

    crushmaps = Table(
        'crushmaps', meta,
        Column('id', Integer, primary_key=True, nullable=False),
        Column('updated_at', DateTime(timezone=False)),
        Column('created_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('deleted', Boolean(create_constraint=True, name=None)),
        Column('content',
                Text(convert_unicode=False,
                    unicode_error=None, _warn_on_bytestring=False),
                nullable=False),
    )

    recipes = Table(
        'recipes', meta,
        Column('id', Integer, primary_key=True, nullable=False),
        Column('recipe_name', String(length=255), unique=True, nullable=False),
        Column('updated_at', DateTime(timezone=False)),
        Column('created_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('deleted', Boolean(create_constraint=True, name=None)),
        Column('pg_num', Integer, nullable=False),
        Column('pgp_num', Integer, nullable=False),
        Column('size', Integer, nullable=False),
        Column('min_size', Integer),
        Column('crush_ruleset', Integer, nullable=False),
        Column('crash_replay_interval', Integer),
    )

    vsm_capacity_manages = Table(
        'vsm_capacity_manages', meta,
        Column('id', Integer, primary_key=True, nullable=False),
        Column('name', String(length=255), nullable=False),
        Column('capacity_quota_mb', Integer),
        Column('capacity_used_mb', Integer),
        Column('updated_at', DateTime(timezone=False)),
        Column('created_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('deleted', Boolean(create_constraint=True, name=None)),
        Column('testyr', Integer),
    )

    try:
        crushmaps.create()
    except Exception:
        meta.drop_all(tables=[crushmaps])
        raise

    try:
        recipes.create()
    except Exception:
        meta.drop_all(tables=[recipes])
        raise

    try:
        vsm_capacity_manages.create()
    except Exception:
        meta.drop_all(tables=[vsm_capacity_manages])
        raise

def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    crushmaps = Table('crushmaps',
                        meta,
                        autoload=True)
    crushmaps.drop()

    recipes = Table('recipes',
                    meta,
                    autoload=True)
    recipes.drop()

    vsm_capacity_manages = Table('vsm_capacity_manages',
                                meta,
                                autoload=True)
    vsm_capacity_manages.drop()
