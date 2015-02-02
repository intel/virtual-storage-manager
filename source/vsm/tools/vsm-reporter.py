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

    def __init__(self,fpath='spot_info_list'):

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
            if not single_line.startswith("#") and len(single_line):
                self._lines.append(single_line)

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
        for pos in range(rpos + 1, len(self._lines)):
            single_line = self._lines[pos]
            if single_line.find("[")!=-1:
                break
            if single_line.startswith("@"):
                value_list.append(single_line.split("=",1))
            elif single_line.startswith("/"):
                value_list.append(str(single_line))
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
    (status, output) = commands.getstatusoutput('./get_storage')
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

    controller_dir='%s/vsm_controller'%(temp_dir)
    (status, output) = commands.getstatusoutput('mkdir -p %s '%(controller_dir))
    storage_dir='%s/storage_hosts'%(temp_dir)
    db_dir='%s/database'%(temp_dir)
    #print "value====",value
    (status, output) = commands.getstatusoutput('mkdir -p %s '%(db_dir))
    for node in storage_nodes:
        cmd_str='mkdir -p %s/%s '%(storage_dir,node)
        (status, output) = commands.getstatusoutput(cmd_str)
        if status!=0:
            print "error cmd ---",cmd_str
            print "error info --",output
    cluster_monitor_dir='%s/ceph_cluster_monitor'%(temp_dir)
    (status, output) = commands.getstatusoutput('mkdir -p %s '%(cluster_monitor_dir))
    cmd_str="mkdir -p %s/os"%controller_dir
    (status, output) = commands.getstatusoutput(cmd_str)
    for node in ceph_nodes:
        cmd_str="mkdir -p %s/%s/os"%(storage_dir,node)
        (status, output) = commands.getstatusoutput(cmd_str)
    vsmcheck_dir='%s/vsm_check_result'%(temp_dir)
    (status, output) = commands.getstatusoutput('mkdir -p %s '%(vsmcheck_dir))

    if cfg_dict.has_key("vsm_controller_node"):
        print "---------------vsm_controller_node-----------------"
        for value in cfg_dict["vsm_controller_node"]:
            if type(value)==str:
                cmd_str='cp %s  %s'%(value,controller_dir)
            elif type(value)==list:
                cmd_str='%s > %s/%s'%(value[1],controller_dir,value[0][1:])
            (status, output) = commands.getstatusoutput(cmd_str)
            if status!=0:
                print "error cmd ---",cmd_str
                print "error info --",output
        print "---------------finished"

    if cfg_dict.has_key("storage_nodes"):
        print "---------------storage_nodes-----------------"
        for value in cfg_dict["storage_nodes"]:
            if type(value)==str:
                for node in storage_nodes:
                    cmd_str='scp %s:%s  %s/%s/'%(node,value,storage_dir,node)
                    (status, output) = commands.getstatusoutput(cmd_str)
                    if status!=0:
                        print "error cmd ---",cmd_str
                        print "error info --",output
            elif type(value)==list:
                for node in storage_nodes:
                    cmd_str="""ssh %s " %s >/tmp/%s " """%(node,value[1],value[0][1:])
                    (status, output) = commands.getstatusoutput(cmd_str)
                    cmd_str="""scp  %s:/tmp/%s %s/ """%(node,value[0][1:],cluster_monitor_dir)
                    (status, output) = commands.getstatusoutput(cmd_str)
                    if status!=0:
                        print "error cmd ---",cmd_str
                        print "error info --",output
        print "---------------finished"

    if cfg_dict.has_key("ceph_cluster_monitor"):
        print "---------------ceph_cluster_monitor-----------------"
        for value in cfg_dict["ceph_cluster_monitor"]:
            if type(value)==list:
                if len(value)!=2:continue
                if value[0].find("crushmap")!=-1:
                    cmd_str="""ssh %s "ceph osd getcrushmap -o /tmp/%s " """%(mon_nodes[0],value[0][1:])
                else:
                    cmd_str="""ssh %s " %s >/tmp/%s " """%(mon_nodes[0],value[1],value[0][1:])
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                     print "error cmd ---",cmd_str
                     print "error info --",output
                time.sleep(5)
                cmd_str="""scp  %s:/tmp/%s %s/ """%(mon_nodes[0],value[0][1:],cluster_monitor_dir)
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0: 
                    print "error cmd ---",cmd_str
                    print "error info --",output
            elif type(value)==str:
                cmd_str="""scp  %s:%s %s/ """%(mon_nodes[0],value,cluster_monitor_dir)    
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                     print "error cmd ---",cmd_str
                     print "error info --",output
        print "---------------finished"

    if cfg_dict.has_key("database"):
        print "---------------database-----------------"
        for value in cfg_dict["database"]:
            if type(value)==list and  value[1].find("vsm-backup.sql")>=0:
                cmd_str="""mysqldump -uroot -p`cat /etc/vsmdeploy/deployrc | grep ROOT | awk -F "=" '{print $2}'` --opt --events --all-databases > %s/%s"""%(db_dir,value[0][1:])
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                     print "error cmd ---",cmd_str
                     print "error info --",output
            elif type(value)==str:
                cmd_str= "cp %s %s"%(value,db_dir)
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                    print "error cmd ---",cmd_str
                    print "error info --",output
        print "---------------finished"

    if cfg_dict.has_key("vsm_check_result"):
        print "---------------vsm_check_result-----------------"
        for value in cfg_dict["vsm_check_result"]:
            if   type(value)==list and value[1].startswith("vsm-check"):
                cmd_str="""%s -d %s/ """%(value[1],vsmcheck_dir)
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0:
                    print "error cmd ---",cmd_str
                    print "error info --",output
                    break
                for i in range(20):
                    time.sleep(10)
                    check_status= [os.path.exists("%s/%s_result"%(vsmcheck_dir,node)) for node in ceph_nodes]
                    if False in check_status:
                        print "wait---",20-i
                    else:
                        break
            else:pass

        for node in ceph_nodes:
            cmd_str="mv %s/%s_result %s/%s/os/vsm-check"%(vsmcheck_dir,node,storage_dir,node)
            (status, output) = commands.getstatusoutput(cmd_str)
        cmd_str="mv %s/*_result %s/os/vsm-check"%(vsmcheck_dir,controller_dir)
        (status, output) = commands.getstatusoutput(cmd_str)
        print "---------------finished"

    if cfg_dict.has_key("os_info_all_nodes"):
        print "----------------os_info_all_nodes----------------"
        for value in cfg_dict["os_info_all_nodes"]:
            if type(value)==list:
                if len(value)!=2:continue
                for node in ceph_nodes:
                    cmd_str="""ssh %s " %s >/tmp/%s " """%(node,value[1],value[0][1:])
                    (status, output) = commands.getstatusoutput(cmd_str)
                    if status!=0: 
                        print "error cmd ---",cmd_str
                        print "error info --",output
                    cmd_str="""scp  %s:/tmp/%s %s/%s/os/ """%(node,value[0][1:],storage_dir,node)
                    (status, output) = commands.getstatusoutput(cmd_str)
                    if status!=0: 
                        print "error cmd ---",cmd_str
                        print "error info --",output
                cmd_str=""" %s >%s/os/%s """%(value[1],controller_dir,value[0][1:])
                (status, output) = commands.getstatusoutput(cmd_str)
                if status!=0: 
                    print "error cmd ---",cmd_str
                    print "error info --",output
            elif type(value)==str:
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

