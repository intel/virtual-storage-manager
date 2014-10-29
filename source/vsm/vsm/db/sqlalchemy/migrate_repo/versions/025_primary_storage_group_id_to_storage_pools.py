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

from sqlalchemy import and_, String, Column, MetaData, select, Table, Integer

def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    storage_pools = Table('storage_pools', meta, autoload=True)
    primary_storage_group_id = Column('primary_storage_group_id', Integer)

    storage_pools.create_column(primary_storage_group_id)

    storage_groups = Table('storage_groups', meta, autoload=True)

    #set storage_pools.primary_stoarge_group_id = storage_group.id
    # set instances.node = compute_nodes.hypervisore_hostname
    q = select(
            [storage_pools.c.id, storage_groups.c.id],
            whereclause=and_(
                storage_pools.c.deleted != True,
                storage_groups.c.deleted != True),
            from_obj=storage_pools.join(storage_groups,
                     storage_pools.c.crush_ruleset == storage_groups.c.rule_id))
    for (storage_pool_id, storage_group_id) in q.execute():
        storage_pools.update().where(storage_pools.c.id == storage_pool_id).\
                                values(primary_storage_group_id=storage_group_id).\
                                execute()  

def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    storage_pools = Table('storage_pools', meta, autoload=True)

    storage_pools.drop_column('primary_storage_group_id')
