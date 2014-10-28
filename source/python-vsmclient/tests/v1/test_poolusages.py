
# Copyright 2014 Intel Corporation, All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the"License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

from vsmclient.v1 import client
from vsmclient.v1 import pool_usages

class ExtensionManager:
    def __init__(self, name, manager_class):
        self.name = name
        self.manager_class = manager_class

vsmclient = client.Client(
                 'vsm',
                 'keystone_vsm_password',
                 'service',
                 auth_url='http://127.0.0.1:5000/v2.0/',
                 extensions=[ExtensionManager('PoolUsageManager',
                                                pool_usages.PoolUsageManager)])
#
pool_id = ['1', '2', '3']
post = vsmclient.PoolUsageManager.create(pool_id)

print post

get = vsmclient.PoolUsageManager.list()
print get

for i in get:
    i.update(attach_status='success')

j = 0
for i in get:
    if j % 2 == 0:
        i.delete()
    j += 1

get = vsmclient.PoolUsageManager.list()
print get

