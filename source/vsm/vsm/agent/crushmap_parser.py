# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright 2012 Red Hat, Inc.
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

"""Crush map parser..

Parse crush map in json format, and identify storage groups from ruleset.

"""
import json
import operator

class CrushMap():

    def __init__(self, json_file=None, json_context=None):
        if json_file:
            with open(json_file, 'r') as fh:
                crush_map = json.load(fh)
            pass
        elif json_context:
            crush_map = json.loads(json_context)
        self._tunables = crush_map['tunables']
        self._devices = crush_map['devices']
        self._rules = crush_map['rules']
        self._types = crush_map['types']
        self._buckets = crush_map['buckets']


    def get_all_tunables(self):
        return self._tunables

    def get_tunable_value(self, parameter):
        return self._tunables[parameter]

    def get_all_types(self):
        return self._types

    def get_type_by_name(self, typename):
        return filter(lambda item: typename == item['name'], self._types)[0]

    def get_all_buckets(self):
        return self._buckets

    def get_weight_by_osd_name(self,osd_name):
        osds = self._devices
        osd_id = [osd['id'] for osd in osds if osd['name'] == osd_name]
        buckets = self._buckets
        for bucket in buckets:
            for item in bucket['items']:
                if item['id'] == osd_id:
                    return item['weight']
        return 'no osd:%s'%osd_name

    def get_bucket_by_id(self, id):
        return filter(lambda item: id == item['id'], self._buckets)[0]

    def get_buckets_by_type(self, typename):
        type = self.get_type_by_name(typename)
        if type:
            type_id = type['type_id']
            return filter(lambda item: type_id == item['type_id'], self._buckets)
        else:
            return []

    def get_buckets_by_name(self, name):
        for bucket in self._buckets:
            if name == bucket['name']:
                return bucket

    def get_children_by_type(self, id, type):
        children = []
        bucket = self.get_bucket_by_id(id)

        for item in bucket['items']:
            child = self.get_bucket_by_id(item['id'])
            if type == child['type_name']:
                children.append(child)

        return children

    def get_all_rules(self):
        return self._rules

    def get_rules_by_name(self, name):
        for rule in self._rules:
            if name == rule['rule_name']:
                return rule
        return None

    def get_rules_by_id(self, rule_id):
        for rule in self._rules:
            if rule_id == rule['rule_id']:
                return rule

    def get_osd_by_id(self, id):
        osd = filter(lambda item: id == item['id'], self._devices)
        if osd:
            return osd[0]

    def get_all_osds_by_rule(self, name):
        rule = self.get_rules_by_name(name)
        steps = rule and rule['steps'] or []
        devices = []
        for step in steps:
            if step['op'] == 'take':
                bucket_id = step['item']
                self.get_all_osds_by_bucket(bucket_id, devices)
        return devices

    def osd_count_by_rule_id(self,rule_id):
        rule = self.get_rules_by_id(rule_id)
        steps = rule['steps']
        devices = []
        for step in steps:
            if step['op'] == 'take':
                bucket_id = step['item']
                self.get_all_osds_by_bucket(bucket_id, devices)
        return len(devices)


    def get_all_osds_by_bucket(self, id, devices):
        print id
        if id >=0 :
            osd = self.get_osd_by_id(id)
            devices.append(osd)
        else :
            bucket = self.get_bucket_by_id(id)
            if bucket :
                items = bucket['items']
                for item in items:
                    self.get_all_osds_by_bucket(item['id'], devices)

        return devices

    def get_bucket_root_by_rule_name(self, rule_name):
        '''
        this function will try to get bucket root for ec pool from storage group
        :param rule:
        :return:
        '''
        rule = self.get_rules_by_name(rule_name)
        bucket_root = "default"

        if len(rule['steps']) > 0:
            step = rule['steps'][0]
            bucket_root = step['item_name']

        return bucket_root

    def get_storage_groups_by_rule(self, rule):
        '''
        this function will execute each op.in detail,
            - op: take  --> the start of an new search
            - op: chooseleaf_firstn/... --> the rule to search
            - op: emit --> the end of a search
        '''
        storage_groups = []
        buckets = []
        sg_count = 0

        for step in rule['steps']:
            op = step['op']
            if op == 'take':
                sg_count += 1
                storage_groups.append([])
                take_bucket = self.get_bucket_by_id(step['item'])
                if take_bucket:
                    buckets.append(take_bucket)
                else:
                    return "undefined error:item %s"%(str(step['item']))

            if op in ['choose_firstn', 'chooseleaf_firstn', 'choose_indep', 'chooseleaf_indep']:
                type = step['type']
                children = []
                for bucket in buckets:
                    temp_buckets = self.get_children_by_type(bucket['id'], type)
                    for temp_bucket in temp_buckets:
                        children.append(temp_bucket)

                buckets = children

            if op == 'emit':
                if sg_count <= 0 :
                    return "invalid crush map format, take and emit is not in pair"
                for bucket in buckets:
                    devices = []
                    storage_groups[sg_count-1] = self.get_all_osds_by_bucket(bucket['id'],devices)

        print storage_groups
        return storage_groups

    def get_storage_group_value_by_rule_name(self,rule_name):
        rule = self.get_rules_by_name(rule_name)
        values = self.get_storage_groups_dict_by_rule([rule])
        return values

    def get_storage_groups_dict_by_rule(self, rules):
        '''
        this function will execute each op.in detail,
            - op: take  --> the start of an new search
            - op: chooseleaf_firstn/... --> the rule to search
            - op: emit --> the end of a search
        '''
        storage_groups = []
        for rule in rules:
            index = -1
            steps_len = len(rule['steps'])
            for i in range(steps_len):
                step = rule['steps'][i]
                op = step['op']
                if op == 'take':
                    bucket_id =  step['item']
                    index = index + 1
                    next_step = rule['steps'][i+1]
                    values = {'name': rule['rule_name'],
                              'choose_num': next_step.get('num',None) or 0,
                              'choose_type': next_step.get('type',None) or '',
                              'take_id': bucket_id,
                              'rule_id': rule['rule_id'],
                              'take_order': index,
                              }
                    storage_groups.append(values)

        return storage_groups

    def _get_location_by_osd_name_list(self,osd_name_list):
        parent_bucket = []
        osds = self._devices
        buckets = self._buckets
        for osd_name in osd_name_list:
            osd_id = [osd['id'] for osd in osds if osd['name'] == osd_name]
            for bucket in buckets:
                for item in bucket['items']:
                    if item['id'] == osd_id:
                        parent_bucket.append(bucket['id'])
        return list(set(parent_bucket))


    def _get_location_by_osd_name(self,osd_name):
        parent_bucket = {}
        osds = self._devices
        buckets = self._buckets
        osd_id = [osd['id'] for osd in osds if osd['name'] == osd_name]
        osd_id = osd_id[0]
        for bucket in buckets:
            for item in bucket['items']:
                if int(item['id']) == int(osd_id):
                    parent_bucket['name'] = bucket['name']
                    parent_bucket['type_name'] = bucket['type_name']
                    break
        return parent_bucket

    def get_parent_bucket_by_name(self, name):
        parent_bucket = {}
        self_bucket = self.get_buckets_by_name(name)
        if self_bucket:
            bucket_id = self_bucket['id']
            buckets = self._buckets
            for bucket in buckets:
                for item in bucket['items']:
                    if int(bucket_id) == int(item['id']):
                        parent_bucket['id'] = bucket['id']
                        parent_bucket['name'] = bucket['name']
                        parent_bucket['type_name'] = bucket['type_name']
                        break
        return parent_bucket

    def get_zone_id_by_host_name(self, host_name):
        zone = self.get_parent_bucket_by_name(host_name)
        return zone['id'] if zone else None

    def get_zone_id_by_osd_name(self, osd_name):
        host_bucket = self._get_location_by_osd_name(osd_name)
        host_name = host_bucket['name']
        return self.get_zone_id_by_host_name(host_name)

    def _show_as_tree_dict(self):
        buckets = self._buckets
        tree_data = {}
        types = self._types
        types.sort(key=operator.itemgetter('type_id'))
        for bucket in buckets:
            node_id = bucket['id']
            items = bucket['items']
            if not tree_data.has_key(str(node_id)):
                node_name = bucket['name']
                node_type_id = bucket['type_id']
                tree_node_data = {'id':node_id,'name':node_name,'type':node_type_id,'type_name':bucket['type_name']}
                tree_data[str(node_id)] = tree_node_data
            for item in items:
                item_id = item['id']
                if self.get_osd_by_id(item_id):
                    item_node = self.get_osd_by_id(item_id)
                    item_node['type_id'] = types[0]['type_id']
                    item_node['type_name'] = types[0]['name']
                elif self.get_bucket_by_id(item_id):
                    item_node = self.get_bucket_by_id(item_id)
                else:
                    return 'No defined error in crushmap:id=%s'%item_id
                item_node_id = item_node['id']
                item_node_parent_id = [node_id]
                if tree_data.has_key(str(item_node_id)):
                    tree_data[str(item_node_id)]['parent_id'] = tree_data[str(item_node_id)].get('parent_id',[])+item_node_parent_id
                else:
                    item_node_name = item_node['name']
                    item_node_type_id = item_node['type_id']
                    item_node_type_name = item_node['type_name']
                    item_tree_node_data = {'id':item_node_id,'name':item_node_name,'type':item_node_type_id,'type_name':item_node_type_name,'parent_id':item_node_parent_id}
                    tree_data[str(item_node_id)] = item_tree_node_data

        return tree_data.values()






if __name__ == '__main__':
    crushmap = CrushMap("./crush.json")
    # print '-----tree_data------'
    # crushmap._show_as_tree_dict()
    # print '=========tree_data================'
    # tunables = crushmap.get_all_tunables()
    ret = crushmap._get_location_by_osd_name('osd.1')
    print 'location----%s-'%ret

    bucket_root = crushmap.get_bucket_root_by_rule_id('performance')
    print 'bucket root = %s' %bucket_root

    ret = crushmap.get_storage_group_value_by_rule_name('ecpooltest3')
    print 'ecpooltest3---storage_group===',ret

#    for name in tunables:
#        print name, tunables[name]
#    print crushmap.get_tunable_value('profile')
#    buckets = crushmap.get_all_buckets()
#    bucket = crushmap.get_buckets_by_name('ceph01_high_performance_test_zone0')
#    print bucket

#    print crushmap.get_all_types()
#    print crushmap.get_all_buckets()
#    buckets = crushmap.get_buckets_by_type('zone')
#    print type(buckets)

#    print crushmap.get_rules_by_name('capacity')
#    crushmap.get_all_osds_by_rule('capacity')
#    print crushmap.get_bucket_by_id(-15)

#    print crushmap.get_rules_by_name('performance')

#    print crushmap.get_all_osds_by_bucket(-15, [])
#    bucket = crushmap.get_bucket_by_id(-15)
#    print bucket
#    print crushmap.get_children_by_type(-15, 'zone')
#     rule = crushmap.get_rules_by_name('value')
#     crushmap.get_storage_groups_by_rule(rule)
