
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

#str0 = "0 data,1 metadata,2 rbd,3 testpool1,4 testpool2,5 -help,6 testpool3,"
import os

str0 = os.popen("ssh root@10.239.82.125 \'ceph osd lspools\' ").read()
print str0
str = str0[0:-2]
print str
items = str.split(',')
print items
test_list = []
for i in items:
    x = i.split()
    test_list.append(x[1])
    print x[1]
print test_list
if 'metadata' in test_list:
    print 'success'

attr_names = ['size', 'min_size', 'crash_replay_interval', 'pg_num',
                     'pgp_num', 'crush_ruleset',]
pool_name = 'testpool2'
values = {}
for attr_name in attr_names:
    val = os.popen("ssh root@10.239.82.125 \'ceph osd pool\
                    get %s %s\'" % (pool_name, attr_name)).read()
    print val
    _list = val.split(':')
    values[attr_name] = int(_list[1])
    print(_list[0])
    print(_list[1])
print values        
