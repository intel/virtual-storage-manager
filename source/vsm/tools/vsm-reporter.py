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
Spot Info  config  file parser.
"""

import os
from vsm.manifest import sys_info
from vsm import exception
from vsm import db


class SpotInfoListParser(object):
    """To parse spot report info config file
    """

    def __init__(self,fpath='/usr/local/bin/spot_info_list'):

        """Set the file path, and which file to parser."""

        self.sections = ['database','vsm_check_result','vsm_controller_node','storage_nodes','os_info_all_nodes','ceph_cluster_monitor']
        self._file_path = fpath
        #if not os.path.exists(self._file_path):
        self._lines = None
        self._read_lines()
        self._map = {}

    def _read_lines(self):

        """Read self._file_path and return the lines needed.

        Need to do filter operations:
            1. lines full with spaces
            2. comments
            3. comments starts with spaces.
        """
        lines = open(self._file_path).readlines()
        self._lines = []
        for single_line in lines:
            single_line = single_line.replace('\n',' ')
            #print "@@@@@@@@@@@",single_line
            if not single_line.startswith("#") and len(single_line):
                self._lines.append(single_line)
        #print "self._lines========",self._lines

    def _check_single_key_word_exists(self, name):

        """Check name exists in this file."""
        # Find the right position of the key word.
        right_pos = -1
        for pos, val in enumerate(self._lines):
            if val.find(name) != -1:
                right_pos = pos
                break

        # If not find, do not raise error to support server_list.
        if right_pos == -1:
            LOG.info("[warning] can not find %s" % name)
            return len(self._lines)

        return right_pos

    def _get_section_value(self,ktype):

        #print "sectione name ======",ktype

        rpos = self._check_single_key_word_exists(ktype)
        value_list=[]
        #print 'rpos=====',rpos,'&&&&&',len(self._lines)
        for pos in range(rpos + 1, len(self._lines)):
            single_line = self._lines[pos]
            #print '********',single_line
            if single_line.find("[")!=-1:
                #print 'break------',single_line
                break
            value_list.append(single_line)
        return value_list

    def format_to_json(self):

        """Transfer the manifest file into json format dict"""

        for section in self.sections:
            self._map[section]=self._get_section_value(section)       
        return self._map





import commands
import datetime
import time


if __name__ == '__main__': 
    cfg_parser=SpotInfoListParser()
    cfg_parser.format_to_json()
    cfg_dict=cfg_parser._map
    #print 'cfg_dict===',cfg_dict
    temp_dir='/opt/vsm_reportor_%s'%(datetime.datetime.now().strftime("%Y%m%d%H%S"))
    print "All the infomation will be in %s"%temp_dir
    (status, output) = commands.getstatusoutput('mkdir -p %s '%temp_dir)
    (status, output) = commands.getstatusoutput('get_storage')
    lines = open("/tmp/ceph_nodes").readlines()
    storage_nodes=[]
    mon_nodes=[]
    for line in lines:
        nodename=line.split(":")[0]
        if line.find("storage")>=0:
            storage_nodes.append(nodename)
        if line.find("monitor")>=0:
            mon_nodes.append(nodename)
    ceph_nodes=storage_nodes+mon_nodes
    ceph_nodes=list(set(ceph_nodes))
    #['vsm_check_result','vsm_controller_node','storage_nodes','os_info_all_nodes','ceph_cluster_monitor','database']

    if cfg_dict.has_key("vsm_controller_node"):
        print "---------------vsm_controller_node-----------------"
        for value in cfg_dict["vsm_controller_node"]:
            controller_dir='%s/vsm_controller'%(temp_dir)
            (status, output) = commands.getstatusoutput('mkdir -p %s '%(controller_dir))
            if value.startswith("/"):
                cmd_str='cp %s  %s'%(value,controller_dir)
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                    print "error cmd ---",cmd_str
                    print "error info --",output
            else:pass
        print "---------------finished"

    if cfg_dict.has_key("storage_nodes"):
        print "---------------storage_nodes-----------------"
        for value in cfg_dict["storage_nodes"]:
            storage_dir='%s/storage_hosts'%(temp_dir)
            for node in storage_nodes:
                cmd_str='mkdir -p %s/%s '%(storage_dir,node)
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                    print "error cmd ---",cmd_str
                    print "error info --",output
            if value.startswith("/"):
                for node in storage_nodes:
                    cmd_str='scp %s:%s  %s/%s/'%(node,value,storage_dir,node)
                    (status, output) = commands.getstatusoutput(cmd_str)
                    if status!=0:
                        print "error cmd ---",cmd_str
                        print "error info --",output
            else:pass
        print "---------------finished"

    if cfg_dict.has_key("ceph_cluster_monitor"):
        print "---------------ceph_cluster_monitor-----------------"
        for value in cfg_dict["ceph_cluster_monitor"]:
            cluster_monitor_dir='%s/ceph_cluster_monitor'%(temp_dir)
            (status, output) = commands.getstatusoutput('mkdir -p %s '%(cluster_monitor_dir))
            if not value.startswith("/"):
                valuelist=value.split(";")
                if len(valuelist)!=2:continue
                if valuelist[0].find("crushmap")!=-1:
                    cmd_str="""ssh %s "ceph osd getcrushmap -o /tmp/%s " """%(mon_nodes[0],valuelist[1])
                else:
                    cmd_str="""ssh %s " %s >/tmp/%s " """%(mon_nodes[0],valuelist[0],valuelist[1])
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                     print "error cmd ---",cmd_str
                     print "error info --",output
                time.sleep(10)
                cmd_str="""scp  %s:/tmp/%s %s/ """%(mon_nodes[0],valuelist[1],cluster_monitor_dir)
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0: 
                    print "error cmd ---",cmd_str
                    print "error info --",output
            else:
                cmd_str="""scp  %s:%s %s/ """%(mon_nodes[0],value,cluster_monitor_dir)    
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                     print "error cmd ---",cmd_str
                     print "error info --",output
        print "---------------finished"

    if cfg_dict.has_key("database"):
        print "---------------database-----------------"
        for value in cfg_dict["database"]:
            db_dir='%s/database'%(temp_dir)
            #print "value====",value
            (status, output) = commands.getstatusoutput('mkdir -p %s '%(db_dir))
            if value.find("vsm-backup.sql")>=0:
                cmd_str="""mysqldump -uroot -p`cat /etc/vsmdeploy/deployrc | grep ROOT | awk -F "=" '{print $2}'` --opt --events --all-databases > %s/vsm-backup.sql"""%db_dir
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                     print "error cmd ---",cmd_str
                     print "error info --",output
            elif value.startswith("/"):
                cmd_str= "cp %s %s"%(value,db_dir)
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                    print "error cmd ---",cmd_str
                    print "error info --",output
        print "---------------finished"

    if cfg_dict.has_key("vsm_check_result"):
        print "---------------vsm_check_result-----------------"
        vsmcheck_dir='%s/vsm_check_result'%(temp_dir)
        (status, output) = commands.getstatusoutput('mkdir -p %s '%(vsmcheck_dir))
        for value in cfg_dict["vsm_check_result"]:
            if  value.startswith("vsm-check"):
                (status, output) = commands.getstatusoutput("""%s -d %s/ """%(value,vsmcheck_dir))
                for i in range(20):
                    check_status= [os.path.exists("%s/%s_result"%(vsmcheck_dir,node)) for node in ceph_nodes]
                    for node_status in check_status:
                        if not node_status:
                            print "wait---",20-i
                            time.sleep(10)
                            continue
                        break
                    break
            else:pass

        for node in ceph_nodes:
            cmd_str="mv %s/%s_result %s/%s/vsm-check"%(vsmcheck_dir,node,storage_dir,node)
            (status, output) = commands.getstatusoutput(cmd_str)
        cmd_str="mv %s/*_result %s/vsm-check"%(vsmcheck_dir,controller_dir)
        (status, output) = commands.getstatusoutput(cmd_str)
        print "---------------finished"

    if cfg_dict.has_key("os_info_all_nodes"):
        print "----------------os_info_all_nodes----------------"
        for value in cfg_dict["os_info_all_nodes"]:
            cmd_str="mkdir -p %s/os"%controller_dir
            (status, output) = commands.getstatusoutput(cmd_str)
            for node in ceph_nodes:
                cmd_str="mkdir -p %s/%s/os"%(storage_dir,node)
                (status, output) = commands.getstatusoutput(cmd_str)
            if not value.startswith("/"):
                valuelist=value.split(";")
                if len(valuelist)!=2:continue
                for node in ceph_nodes:
                    cmd_str="""ssh %s " %s >/tmp/%s " """%(node,valuelist[0],valuelist[1])
                    (status, output) = commands.getstatusoutput(cmd_str)
                    if status!=0: 
                        print "error cmd ---",cmd_str
                        print "error info --",output
                    cmd_str="""scp  %s:/tmp/%s %s/%s/os/ """%(node,valuelist[1],storage_dir,node)
                    (status, output) = commands.getstatusoutput(cmd_str)
                    if status!=0: 
                        print "error cmd ---",cmd_str
                        print "error info --",output
                cmd_str=""" %s >%s/os/%s """%(valuelist[0],controller_dir,valuelist[1])
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0: 
                    print "error cmd ---",cmd_str
                    print "error info --",output
            else:
                for node in ceph_nodes:
                    cmd_str="""scp  %s:%s %s/%s/os/ """%(node,value,storage_dir,node)
                    (status, output) = commands.getstatusoutput(cmd_str)
                cmd_str="""cp  %s %s/os/ """%(value,controller_dir)
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0: 
                    print "error cmd ---",cmd_str
                    print "error info --",output
        print "---------------finished"
        print "Please send this information to us.Thanks!"
