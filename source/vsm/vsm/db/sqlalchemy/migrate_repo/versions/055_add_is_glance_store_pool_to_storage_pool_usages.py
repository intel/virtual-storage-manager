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

from sqlalchemy import Boolean, Column
from sqlalchemy import MetaData
from sqlalchemy import Table

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine;
    # bind migrate_engine to your metadata
    meta = MetaData()
    meta.bind = migrate_engine

    storage_pool_usages = Table('storage_pool_usages', meta, autoload=True)

    as_glance_store_pool = Column('as_glance_store_pool', Boolean, default=False)
    try:
        storage_pool_usages.create_column(as_glance_store_pool)
    except Exception:
        raise

def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    storage_pool_usages = Table('storage_pool_usages', meta, autoload=True)

    as_glance_store_pool = Column('as_glance_store_pool', Boolean, default=False)
    try:
        storage_pool_usages.drop_column(as_glance_store_pool)
    except Exception:
        raise
