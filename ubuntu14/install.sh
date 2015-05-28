#!/bin/bash

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

#-------------------------------------------------------------------------------
#            Usage
#-------------------------------------------------------------------------------

function usage() {
    cat << EOF
Usage: install.sh

Auto deploy vsm:
    The tool can help you to deploy the vsm envirement automatically.
    Please run such as bash +x install.sh

Options:
  --help | -h
    Print usage information.
  --manifest [manifest directory] | -m [manifest directory]
    The directory to store the server.manifest and cluster.manifest.
  --version [master] | -v [master]
    The version of vsm dependences to download(Default=master).
  --user | -u
    The user will be used to connect remote nodes to deploy vsm
EOF
    exit 0
}

MANIFEST_PATH=""
dependence_version="master"
USER=`whoami`
while [ $# -gt 0 ]; do
  case "$1" in
    -h) usage ;;
    --help) usage ;;
    -m| --manifest) shift; MANIFEST_PATH=$1 ;;
    -v| --version) shift; dependence_version=$1 ;;
    -u| --user) shift; USER=$1 ;;
    *) shift ;;
  esac
  shift
done


set -e
set -o xtrace

echo "Before auto deploy the vsm, please be sure that you have set the manifest 
such as manifest/192.168.100.100/server.manifest. And you have changed the file, too."
sleep 5

TOPDIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null; mkdir -p $TEMP;

HOSTNAME=`hostname`
#HOSTIP=`hostname -I|sed s/[[:space:]]//g`
HOSTIP=`hostname -I`

source $TOPDIR/hostrc

is_controller=0
for ip in $HOSTIP; do
    if [ $ip == $controller_ip ]; then
        is_controller=1
    fi
done

if [ $is_controller -eq 0 ]; then
    echo "[Info]: You run the tool in a third server."
else
    echo "[Info]: You run the tool in the controller server."
fi


#-------------------------------------------------------------------------------
#            checking packages
#-------------------------------------------------------------------------------

echo "+++++++++++++++start checking packages+++++++++++++++"

if [ ! -d vsmrepo ]; then
    echo "You should have the vsmrepo folder, please check and try again"
    exit 1
fi

cd vsmrepo
is_python_vsmclient=`ls|grep python-vsmclient*.deb|wc -l`
is_vsm=`ls|grep -v python-vsmclient|grep -v vsm-dashboard|grep -v vsm-deploy|grep vsm|wc -l`
is_vsm_dashboard=`ls|grep vsm-dashboard*.deb|wc -l`
is_vsm_deploy=`ls|grep vsm-deploy*.deb|wc -l`
if [ $is_python_vsmclient -gt 0 ] && [ $is_vsm -gt 0 ] && [ $is_vsm_dashboard -gt 0 ] && [ $is_vsm_deploy -gt 0 ]; then
    echo "The vsm pachages have been already prepared"
else
    echo "please check the vsm packages, then try again"
    exit 1
fi

cd $TOPDIR
echo "+++++++++++++++finish checking packages+++++++++++++++"


##-------------------------------------------------------------------------------
##            setting the iptables and selinux
##-------------------------------------------------------------------------------
#
#echo "+++++++++++++++start setting the iptables and selinux+++++++++++++++"
#
#function set_iptables_selinux() {
#    ssh $USER@$1 "service iptables stop"
#    ssh $USER@$1 "chkconfig iptables off"
#    ssh $USER@$1 "sed -i \"s/SELINUX=enforcing/SELINUX=disabled/g\" /etc/selinux/config"
##    ssh $USER@$1 "setenforce 0"
#}
#
#if [ $is_controller -eq 0 ]; then
#    set_iptables_selinux $controller_ip
#else
#    service iptables stop
#    chkconfig iptables off
#    sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config
##    setenforce 0
#fi
#
#for ip in $storage_ip_list; do
#    set_iptables_selinux $ip
#done
#
#echo "+++++++++++++++finish setting the iptables and selinux+++++++++++++++"


#-------------------------------------------------------------------------------
#            downloading the dependences
#-------------------------------------------------------------------------------

if [ ! -d /opt/vsm-dep-repo ] && [ ! -d vsm-dep-repo ]; then
    mkdir -p vsm-dep-repo
    cd vsm-dep-repo
    for i in `cat ../debs.lst`; do
        wget https://raw.githubusercontent.com/01org/vsm-dependencies/$DEPENDENCE_VERSION/ubuntu14/$i
    done
    cd $TOPDIR
fi

#if [ $is_controller -eq 0 ]; then
#    ssh $USER@$controller_ip "rm -rf /opt/vsm-dep-repo"
#    scp -r vsm-dep-repo $USER@$controller_ip:/opt
#else
#    if [ -d vsm-dep-repo ]; then
#        rm -rf /opt/vsm-dep-repo
#        cp -rf vsm-dep-repo /opt
#    fi
#fi


#-------------------------------------------------------------------------------
#            setting the repo
#-------------------------------------------------------------------------------

echo "+++++++++++++++start setting the repo+++++++++++++++"

apt-get update
is_dpkg_dev=`dpkg -s dpkg-dev|grep "install ok installed"|wc -l`
if [[ $is_dpkg_dev -eq 0 ]]; then
    apt-get install -y dpkg-dev
fi

dpkg-scanpackages vsm-dep-repo | gzip > vsm-dep-repo/Packages.gz

#is_apache2=`dpkg -s apache2|grep "install ok installed"|wc -l`
#if [[ is_apache2 -gt 0 ]]; then
#    sed -i "s,#*Listen 80,Listen 80,g" /etc/apache2/ports.conf
#    service apache2 restart
#fi

rm -rf vsm.list
rm -rf vsm-dep.list

cat <<"EOF" >vsm.list
deb file:///opt vsmrepo/
EOF

cat <<"EOF" >vsm-dep.list
deb file:///opt vsm-dep-repo/
EOF

cat <<"EOF" >apt.conf
APT::Get::AllowUnauthenticated 1 ;
EOF

#oldvsmurl="deb file:///opt vsmrepo/"
#oldvsmdepurl="deb file:///opt vsm-dep-repo/"
#newvsmurl="deb http://$controller_ip vsmrepo/"
#newvsmdepurl="deb http://$controller_ip vsm-dep-repo/"
#sed -i "s,$oldvsmurl,$newvsmurl,g" ./vsm.list
#sed -i "s,$oldvsmdepurl,$newvsmdepurl,g" ./vsm-dep.list

if [ $is_controller -eq 0 ]; then
    scp -r vsm-dep-repo $USER@$controller_ip:/opt
    scp -r vsmrepo $USER@$controller_ip:/opt
    scp apt.conf $USER@$controller_ip:/etc/apt
    scp vsm.list $USER@$controller_ip:/etc/apt/sources.list.d
    scp vsm-dep.list $USER@$controller_ip:/etc/apt/sources.list.d
    ssh $USER@$controller_ip "apt-get update"
else
    cp -r vsm-dep-repo /opt
    cp -r vsmrepo /opt
    cp apt.conf /etc/apt
    cp vsm.list /etc/apt/sources.list.d
    cp vsm-dep.list /etc/apt/sources.list.d
    apt-get update
fi

function set_repo() {
    scp -r vsm-dep-repo $USER@$1:/opt
    scp -r vsmrepo $USER@$1:/opt
    ssh $USER@$1 "rm -rf /etc/apt/sources.list.d/vsm.list /etc/apt/sources.list.d/vsm-dep.list"
    scp apt.conf $USER@$1:/etc/apt
    scp vsm.list $USER@$1:/etc/apt/sources.list.d
    scp vsm-dep.list $USER@$1:/etc/apt/sources.list.d
    ssh $USER@$1 "apt-get update"
}

for ip in $storage_ip_list; do
    set_repo $ip
done

echo "+++++++++++++++finish setting the repo+++++++++++++++"


#-------------------------------------------------------------------------------
#            install vsm rpm and dependences
#-------------------------------------------------------------------------------

echo "+++++++++++++++install vsm rpm and dependences+++++++++++++++"

function install_vsm_controller() {
    ssh $USER@$1 "apt-get install -y vsm vsm-deploy vsm-dashboard python-vsmclient"
    ssh $USER@$1 "preinstall"
}

function install_vsm_storage() {
    ssh $USER@$1 "apt-get install -y vsm vsm-deploy"
    ssh $USER@$1 "preinstall"
}

if [ $is_controller -eq 0 ]; then
    install_vsm_controller $controller_ip
else
    apt-get install -y vsm vsm-deploy vsm-dashboard python-vsmclient
    preinstall
fi

for ip in $storage_ip_list; do
    install_vsm_storage $ip
done

echo "+++++++++++++++finish install vsm rpm and dependences+++++++++++++++"


#-------------------------------------------------------------------------------
#            setup vsm controller node
#-------------------------------------------------------------------------------

if [ -z $MANIFEST_PATH ]; then
    MANIFEST_PATH="manifest"
fi

function setup_controller() {
    ssh $USER@$controller_ip "rm -rf /etc/manifest/cluster_manifest"
    scp $MANIFEST_PATH/$controller_ip/cluster.manifest $USER@$controller_ip:/etc/manifest
    ssh $USER@$controller_ip "chown root:vsm /etc/manifest/cluster.manifest; chmod 755 /etc/manifest/cluster.manifest"
    is_cluster_manifest_error=`ssh $USER@$controller_ip "cluster_manifest|grep error|wc -l"`
    if [ $is_cluster_manifest_error -gt 0 ]; then
        echo "please check the cluster.manifest, then try again"
        exit 1
    else
        ssh $USER@$controller_ip "vsm-controller"
    fi
}

if [ $is_controller -eq 0 ]; then
    setup_controller
else
    rm -rf /etc/manifest/cluster.manifest
    cp $MANIFEST_PATH/$controller_ip/cluster.manifest /etc/manifest
    chown root:vsm /etc/manifest/cluster.manifest
    chmod 755 /etc/manifest/cluster.manifest
    if [ `cluster_manifest|grep error|wc -l` -gt 0 ]; then
        echo "please check the cluster.manifest, then try again"
        exit 1
    else
        vsm-controller
    fi
fi


#-------------------------------------------------------------------------------
#            setup vsm storage node
#-------------------------------------------------------------------------------

count_ip=0
for ip in $storage_ip_list; do
    let count_ip=$count_ip+1
done
let count_ip=$count_ip+2+1
if [ `ls $MANIFEST_PATH|wc -l` != $count_ip ]; then
    echo "please check the manifest folder"
    exit 1
fi

success=""
failure=""
if [ $is_controller -eq 0 ]; then
    token=`ssh $USER@$controller_ip "agent-token"`
else
    token=`agent-token`
fi

function setup_storage() {
    ssh $USER@$1 "rm -rf /etc/manifest/server.manifest"
    sed -i "s/token-tenant/$token/g" $MANIFEST_PATH/$1/server.manifest
    old_str=`cat $MANIFEST_PATH/$1/server.manifest| grep ".*-.*" | grep -v by | grep -v "\["`
    sed -i "s/$old_str/$token/g" $MANIFEST_PATH/$1/server.manifest
    scp $MANIFEST_PATH/$1/server.manifest $USER@$1:/etc/manifest
    ssh $USER@$1 "chown root:vsm /etc/manifest/server.manifest; chmod 755 /etc/manifest/server.manifest"
    is_server_manifest_error=`ssh $USER@$1 "server_manifest|grep ERROR|wc -l"`
    if [ $is_server_manifest_error -gt 0 ]; then
        echo "[warning]: The server.manifest in $1 is wrong, so fail to setup in $1 storage node"
        failure=$failure"$1 "
    else
        ssh $USER@$1 "vsm-node"
        success=$success"$1 "
    fi
}

for ip in $storage_ip_list; do
    setup_storage $ip
done


#-------------------------------------------------------------------------------
#            finish auto deploy
#-------------------------------------------------------------------------------

echo "Successful storage node ip: $success"
echo "Failure storage node ip: $failure"

set +o xtrace


# change_log
# Feb 12 2015 Zhu Boxiang <boxiangx.zhu@intel.com> - 2015.2.12-1
# Initial release
# 
#
# 

