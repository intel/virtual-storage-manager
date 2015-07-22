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

    appnodes = Table('appnodes', meta, autoload=True)

    ip = Column('ip', String(length=50), nullable=False)
    os_tenant_name = Column('os_tenant_name', String(length=50), nullable=False)
    os_username = Column('os_username', String(length=50), nullable=False)
    os_password = Column('os_password', String(length=50), nullable=False)
    os_auth_url = Column('os_auth_url', String(length=255), nullable=False)
    os_region_name = Column('os_region_name', String(length=255), nullable=True)

    try:
        appnodes.drop_column(ip)
        appnodes.create_column(os_tenant_name)
        appnodes.create_column(os_username)
        appnodes.create_column(os_password)
        appnodes.create_column(os_auth_url)
        appnodes.create_column(os_region_name)
    except Exception:
        raise

def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    appnodes = Table('appnodes', meta, autoload=True)

    ip = Column('ip', String(length=50), nullable=False)
    os_tenant_name = Column('os_tenant_name', String(length=50), nullable=False)
    os_username = Column('os_username', String(length=50), nullable=False)
    os_password = Column('os_password', String(length=50), nullable=False)
    os_auth_url = Column('os_auth_url', String(length=255), nullable=False)
    os_region_name = Column('os_region_name', String(length=255), nullable=True)

    try:
        appnodes.create_column(ip)
        appnodes.drop_column(os_tenant_name)
        appnodes.drop_column(os_username)
        appnodes.drop_column(os_password)
        appnodes.drop_column(os_auth_url)
        appnodes.drop_column(os_region_name)
    except Exception:
        raise
