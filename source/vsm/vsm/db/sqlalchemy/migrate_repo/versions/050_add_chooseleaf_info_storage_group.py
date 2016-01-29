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

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Integer, MetaData, String
from sqlalchemy import Table, Index

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine;
    # bind migrate_engine to your metadata

    meta = MetaData()
    meta.bind = migrate_engine

    storage_group = Table('storage_groups', meta, autoload=True)
    choose_type = Column('choose_type',String(length=255), nullable=True)
    storage_group.create_column(choose_type)
    choose_num = Column('choose_num',Integer, nullable=True, default=0)
    storage_group.create_column(choose_num)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    storage_group = Table('storage_groups', meta, autoload=True)
    choose_type = Column('choose_type',String(length=255), nullable=True)
    choose_num = Column('choose_num',Integer, nullable=True, default=0)

    try:
        storage_group.drop_column(choose_type)
        storage_group.drop_column(choose_num)
    except Exception:
        raise