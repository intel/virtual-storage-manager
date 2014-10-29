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
from sqlalchemy import Integer, MetaData, String, Text, Table
from vsm.db.sqlalchemy import models

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine;
    # bind migrate_engine to your metadata
    meta = MetaData()
    meta.bind = migrate_engine

    vsmapps = Table(
        'vsmapps', meta,
        Column('id', Integer, primary_key=True, nullable=False),
        Column('user_id', String(length=32), nullable=False),
        Column('project_id', String(length=32), nullable=True, unique=True),
        Column('uuid', String(length=32), nullable=False),
        Column('display_name', String(length=50), nullable=True),
        Column('app_type', String(length=50), default='OpenStack'),
        Column('storage_type', String(length=50), default='rbd'),
        Column('status', String(length=50), nullable=True),
        Column('created_at', DateTime(timezone=False)),
        Column('updated_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('deleted', Boolean(create_constraint=True, name=None), default=False),
    )

    try:
        vsmapps.create()
    except Exception:
        meta.drop_all(tables=[vsmapps])
        raise

def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
    table = Table('vsmapps', meta, autoload=True)
    table.drop()

