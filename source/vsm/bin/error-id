#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2014 Intel
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

"""
Use socket to transfer msg.
"""

import os
import json
import Queue
import vsm
from vsm import utils

def _json_dict(d):
    return json.dumps(d, sort_keys=True, indent=2)

def _to_dict(lines):
    def _all():
        d = []
        for x in lines:
            if x.find('message = _(') != -1:
                continue
            x = x.split(' ')[1]
            x = x.replace('(', ' ')
            x = x.replace(')', ' ')
            x = x.replace(':', ' ')
            part = x.strip().split(' ')
            son = part[0]
            if len(part) == 0:
                parent = None
            else:
                parent = part[1]
            d.append((son, parent))

        return d

    d = {}
    pairs = _all()
    for x in pairs:
        d[x[0]] = None
        d[x[1]] = None

    for x in pairs:
        d[x[0]] = x[1]

    return d

def _get_lines(fp):
    content = utils.execute('cat', fp, run_as_root=True)[0]
    lines = content.split('\n')

    temp = []
    for x in lines:
        if x.startswith('class'):
            temp.append(x)
        if x.startswith('    message = _('):
            temp.append(x)
    return temp

class ErrorID(object):
    def __init__(self):
        self._dict = {}
        vsm_path = os.path.dirname(vsm.__file__)
        expt_file = '%s/exception.py' % vsm_path
        self._lines = _get_lines(expt_file)
        self._dict = _to_dict(self._lines)
        # print json.dumps(self._dict, sort_keys=True, indent=2)
        self._top_parents = None
        self._number = {}
        self._level = {}

    def top_parents(self):
        if self._top_parents:
            return self._top_parents
        self._top_parents = []
        for key in self._dict.keys():
            if not self._dict[key]:
                self._top_parents.append(key)
        self._top_parents = sorted(list(set(self._top_parents)))
        return self._top_parents

    def _get_sons(self, parent):
        sons = []
        for key in self._dict.keys():
            if self._dict[key] == parent:
                sons.append(key)
        sons = sorted(sons)
        return sons

    def _get_cnt(self, name, cnt):
        if not self._dict[name]:
            return str(cnt)

        parent = self._dict.get(name, None)
        pre = self._number.get(parent, '')
        return pre + str(cnt)

    def encode(self):
        q = Queue.Queue(len(self._dict.keys()) + 10)

        cnt = 1
        d = self.top_parents()
        for x in d:
            q.put((x, cnt))
            cnt = cnt + 1

        q.put(('', 0))
        level = 1
        seq = 1

        while (q.empty() == False and q.qsize() > 1):
            tp = q.get()
            name = tp[0]
            num = tp[1]

            if name == '' and num == 0:
                level = level + 1
                q.put(('', 0))
                continue

            seq = seq + 1
            self._number[name] = self._get_cnt(name, num)
            self._level[name] = str(level) + str(seq)
            sons = self._get_sons(name)

            cnt = 1
            for x in sons:
                q.put((x, cnt))
                cnt = cnt + 1

        max_len = 0
        for key in self._number.keys():
            if len(self._number[key]) > max_len:
                max_len = len(self._number[key])

        for key in self._number.keys():
            if len(self._number[key]) <= max_len:
                s = max_len - len(self._number[key])
                self._number[key] = 'E' \
                                    + '0'*s \
                                    + self._number[key] \
                                    + str(self._level[name])

        return self._number

e = ErrorID()
print _json_dict(e.encode())
