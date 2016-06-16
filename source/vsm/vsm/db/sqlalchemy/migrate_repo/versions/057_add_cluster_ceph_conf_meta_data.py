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

from sqlalchemy import Integer, String, Column
from sqlalchemy import MetaData
from sqlalchemy import Table

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine;
    # bind migrate_engine to your metadata
    meta = MetaData()
    meta.bind = migrate_engine

    clusters = Table('clusters', meta, autoload=True)

    ceph_conf_md5sum = Column('ceph_conf_md5sum', String(length=64), nullable=True)
    ceph_conf_luts = Column('ceph_conf_luts', Integer, default=0)

    try:
        clusters.create_column(ceph_conf_md5sum)
        clusters.create_column(ceph_conf_luts)
    except Exception:
        raise

def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    clusters = Table('clusters', meta, autoload=True)

    ceph_conf_luts = Column('ceph_conf_luts', Integer, default=0)
    ceph_conf_md5sum = Column('ceph_conf_md5sum', String(length=64), nullable=True)

    try:
        clusters.drop_column(ceph_conf_luts)
        clusters.drop_column(ceph_conf_md5sum)
    except Exception:
        raise
