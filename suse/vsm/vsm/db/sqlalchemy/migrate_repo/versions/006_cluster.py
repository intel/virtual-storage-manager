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
from sqlalchemy import Integer, MetaData, String, Table
from sqlalchemy import Table, Text

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine;
    # bind migrate_engine to your metadata
    meta = MetaData()
    meta.bind = migrate_engine

    ceph_cluster = Table(
        'clusters', meta,
        Column('id', Integer, primary_key=True, nullable=False),
        #TODO add UUID for cluster. If there are same cluster name.
        Column('name', String(length=255), nullable=True),
        Column('file_system', String(length=255), nullable=True),
        Column('primary_public_network', String(length=255), nullable=True),
        Column('secondary_public_network', String(length=255), nullable=True),
        Column('cluster_network', String(length=255), nullable=True),
        Column('journal_size', Integer, nullable=False),
        Column('size', Integer, nullable=True),
        #[!NOTE!] this field is json format string.
        # At now, it contains keyring.admin content from
        # monitor node.
        Column('info_dict',
               Text(convert_unicode=False,
                    unicode_error=None, _warn_on_bytestring=False),
               nullable=True),
        Column('ceph_conf', Text(length=10485760), nullable=True),
        Column('deleted_times', Integer, nullable=True),
        Column('created_at', DateTime(timezone=False)),
        Column('updated_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('deleted', Boolean(create_constraint=True, name=None)),
    )

    try:
        ceph_cluster.create()
    except Exception:
        meta.drop_all(tables=[ceph_cluster])
        raise

def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    ceph_cluster = Table('clusters',
                    meta,
                    autoload=True)
    ceph_cluster.drop()
