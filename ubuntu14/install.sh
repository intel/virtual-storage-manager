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
    Please run the command like: bash +x install.sh or ./install.sh

Options:
  --help | -h
    Print usage information.
  --manifest [manifest directory] | -m [manifest directory]
    The directory to store the server.manifest and cluster.manifest.
  --repo-path [dependencies path]
    The path of dependencies.
  --version [master] | -v [master]
    The version of vsm dependences to download(Default=master).
  --user | -u
    The user will be used to connect remote nodes to deploy vsm.
  --prepare
    Preparing to install vsm. Checking vsm packages, setting iptables
  and selinux, downloading the dependencies and setting the repository.
  --controller [ip]
    Installing the controller node only.
  --agent [ip,ip]
    Install the agent node(s), like: --agnet ip,ip with no blank.
EOF
    exit 0
}

MANIFEST_PATH=""
REPO_PATH="vsm-dep-repo"
DEPENDENCE_BRANCH="master"
USER=`whoami`
IS_PREPARE=False
IS_CONTROLLER_INSTALL=False
IS_AGENT_INSTALL=False
NEW_CONTROLLER_IP=""
NEW_AGENT_IPS=""

while [ $# -gt 0 ]; do
  case "$1" in
    -h| --help) usage ;;
    -m| --manifest) shift; MANIFEST_PATH=$1 ;;
    -r| --repo-path) shift; REPO_PATH=$1 ;;
    -v| --version) shift; DEPENDENCE_BRANCH=$1 ;;
    -u| --user) shift; USER=$1 ;;
    --prepare) IS_PREPARE=True ;;
    --controller) shift; IS_CONTROLLER_INSTALL=True; NEW_CONTROLLER_IP=$1 ;;
    --agent) shift; IS_AGENT_INSTALL=True; NEW_AGENT_IPS=$1 ;;
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

if [ -z $MANIFEST_PATH ]; then
    MANIFEST_PATH="manifest"
fi

if [[ $NEW_CONTROLLER_IP != "" ]]; then
    controller_ip=$NEW_CONTROLLER_IP
fi

IS_CONTROLLER=0
for ip in $HOSTIP; do
    if [ $ip == $controller_ip ]; then
        IS_CONTROLLER=1
    fi
done

if [ $IS_CONTROLLER -eq 0 ]; then
    echo "[Info]: You run the tool in a third server."
else
    echo "[Info]: You run the tool in the controller server."
fi

#-------------------------------------------------------------------------------
#            prepare
#-------------------------------------------------------------------------------

function check_vsm_package() {
    if [[ ! -d vsmrepo ]]; then
        echo "You must have the vsmrepo folder, please check and try again."
        exit 1
    fi
    cd vsmrepo
    IS_PYTHON_VSMCLIENT=`ls|grep python-vsmclient*.deb|wc -l`
    IS_VSM=`ls|grep -v python-vsmclient|grep -v vsm-dashboard|grep -v vsm-deploy|grep vsm|wc -l`
    IS_VSM_DASHBOARD=`ls|grep vsm-dashboard*.deb|wc -l`
    IS_VSM_DEPLOY=`ls|grep vsm-deploy*.deb|wc -l`
    if [[ $IS_PYTHON_VSMCLIENT -gt 0 ]] && [[ $IS_VSM -gt 0 ]] &&\
        [[ $IS_VSM_DASHBOARD -gt 0 ]] && [[ $IS_VSM_DEPLOY -gt 0 ]]; then
        echo "The vsm pachages have been already prepared"
    else
        echo "please check the vsm packages, then try again"
        exit 1
    fi
    cd $TOPDIR
}

function set_iptables_and_selinux() {
    ssh $USER@$1 "service iptables stop"
    ssh $USER@$1 "chkconfig iptables off"
    ssh $USER@$1 "sed -i \"s/SELINUX=enforcing/SELINUX=disabled/g\" /etc/selinux/config"
    ssh $USER@$1 "setenforce 0"
}

function download_dependencies() {
    if [[ ! -d $REPO_PATH ]]; then
        mkdir -p $REPO_PATH
        cd $REPO_PATH
        for i in `cat $TOPDIR/debs.lst`; do
            wget https://github.com/01org/vsm-dependencies/raw/$DEPENDENCE_BRANCH/ubuntu14/$i
        done
        cd $TOPDIR
    elif [[ -d $REPO_PATH ]]; then
        cd $REPO_PATH
        for i in `cat $TOPDIR/debs.lst`; do
            if [[ `ls |grep $i|wc -l` -eq 0 ]]; then
                wget https://github.com/01org/vsm-dependencies/raw/$DEPENDENCE_BRANCH/ubuntu14/$i
            else
                COUNT=0
                for j in `ls |grep $i`; do
                    if [[ $i == $j ]]; then
                        let COUNT+=1
                    fi
                done
                if [[ $COUNT -eq 0 ]]; then
                    wget https://github.com/01org/vsm-dependencies/raw/$DEPENDENCE_BRANCH/ubuntu14/$i
                fi
            fi
        done
        sudo rm -rf *.deb.*
        cd $TOPDIR
    fi
}

function prepare_repo() {
    sudo apt-get update
    IS_DPKG_DEV=`dpkg -s dpkg-dev|grep "install ok installed"|wc -l`
    if [[ $IS_DPKG_DEV -eq 0 ]]; then
        sudo apt-get install -y dpkg-dev
    fi
    mkdir -p $REPO_PATH/vsm-dep-repo
    cd $REPO_PATH
    cp *.deb vsm-dep-repo
    dpkg-scanpackages vsm-dep-repo | gzip > vsm-dep-repo/Packages.gz
    cd $TOPDIR

    rm -rf vsm.list vsm-dep.list

    cat <<"EOF" >vsm.list
deb file:///opt vsmrepo/
EOF

    cat <<"EOF" >vsm-dep.list
deb file:///opt vsm-dep-repo/
EOF

}

function prepare() {
    check_vsm_package
#    set_iptables_and_selinux
    download_dependencies
    prepare_repo
}

function set_repo() {
    ssh $USER@$1 "sudo rm -rf /etc/apt/sources.list.d/vsm.list /etc/apt/sources.list.d/vsm-dep.list; \
        sudo rm -rf /opt/vsm-dep-repo /opt/vsmrepo"
    scp -r $REPO_PATH/vsm-dep-repo $USER@$1:/tmp
    ssh $USER@$1 "sudo mv /tmp/vsm-dep-repo /opt"
    scp -r vsmrepo $USER@$1:/tmp
    ssh $USER@$1 "sudo mv /tmp/vsmrepo /opt"
    ssh $USER@$1 "if [[ -f /etc/apt/apt.conf ]]; then sudo mv /etc/apt/apt.conf /tmp; \
        sudo echo \"APT::Get::AllowUnauthenticated 1 ;\" >> /tmp/apt.conf; sudo mv /tmp/apt.conf /etc/apt; \
        else touch /tmp/apt.conf; echo \"APT::Get::AllowUnauthenticated 1 ;\" >> /tmp/apt.conf; \
        sudo mv /tmp/apt.conf /etc/apt; fi"
#    scp apt.conf $USER@$1:/etc/apt
    scp vsm.list $USER@$1:/tmp
    ssh $USER@$1 "sudo mv /tmp/vsm.list /etc/apt/sources.list.d"
    scp vsm-dep.list $USER@$1:/tmp
    ssh $USER@$1 "sudo mv /tmp/vsm-dep.list /etc/apt/sources.list.d"
    ssh $USER@$1 "sudo apt-get update"
}

function check_manifest() {
    if [[ $1 == $controller_ip ]]; then
        if [[ ! -d $MANIFEST_PATH/$1 ]] || [[ ! -f $MANIFEST_PATH/$1/cluster.manifest ]]; then
            echo "Please check the manifest, then try again."
            exit 1
        fi
    else
        if [[ ! -d $MANIFEST_PATH/$1 ]] || [[ ! -f $MANIFEST_PATH/$1/server.manifest ]]; then
            echo "Please check the manifest, then try again."
            exit 1
        fi
    fi
}

#-------------------------------------------------------------------------------
#            controller
#-------------------------------------------------------------------------------

function setup_remote_controller() {
    ssh $USER@$controller_ip "sudo rm -rf /etc/manifest/cluster_manifest"
    scp $MANIFEST_PATH/$controller_ip/cluster.manifest $USER@$controller_ip:/tmp
    ssh $USER@$controller_ip "sudo mv /tmp/cluster.manifest /etc/manifest"
    ssh $USER@$controller_ip "sudo chown root:vsm /etc/manifest/cluster.manifest; sudo chmod 755 /etc/manifest/cluster.manifest"
    is_cluster_manifest_error=`ssh $USER@$controller_ip "cluster_manifest|grep error|wc -l"`
    if [ $is_cluster_manifest_error -gt 0 ]; then
        echo "please check the cluster.manifest, then try again"
        exit 1
    else
        ssh $USER@$controller_ip "sudo vsm-controller"
    fi
}

function install_controller() {
    check_manifest $controller_ip
    set_repo $controller_ip
    ssh $USER@$controller_ip "sudo apt-get install -y vsm vsm-deploy vsm-dashboard python-vsmclient"
    ssh $USER@$controller_ip "sudo preinstall"

    if [[ $IS_CONTROLLER -eq 0 ]]; then
        setup_remote_controller
    else
        sudo rm -rf /etc/manifest/cluster.manifest
        sudo cp $MANIFEST_PATH/$controller_ip/cluster.manifest /etc/manifest
        sudo chown root:vsm /etc/manifest/cluster.manifest
        sudo chmod 755 /etc/manifest/cluster.manifest
        if [ `cluster_manifest|grep error|wc -l` -gt 0 ]; then
            echo "please check the cluster.manifest, then try again"
            exit 1
        else
            sudo vsm-controller
        fi
    fi
}

#-------------------------------------------------------------------------------
#            agent
#-------------------------------------------------------------------------------

function setup_remote_agent() {
    ssh $USER@$1 "sudo rm -rf /etc/manifest/server.manifest"
    sudo sed -i "s/token-tenant/$TOKEN/g" $MANIFEST_PATH/$1/server.manifest
    old_str=`cat $MANIFEST_PATH/$1/server.manifest| grep ".*-.*" | grep -v by | grep -v "\["`
    sudo sed -i "s/$old_str/$TOKEN/g" $MANIFEST_PATH/$1/server.manifest
    scp $MANIFEST_PATH/$1/server.manifest $USER@$1:/tmp
    ssh $USER@$1 "sudo mv /tmp/server.manifest /etc/manifest"
    ssh $USER@$1 "sudo chown root:vsm /etc/manifest/server.manifest; sudo chmod 755 /etc/manifest/server.manifest"
    is_server_manifest_error=`ssh $USER@$1 "server_manifest|grep ERROR|wc -l"`
    if [ $is_server_manifest_error -gt 0 ]; then
        echo "[warning]: The server.manifest in $1 is wrong, so fail to setup in $1 storage node"
    else
        ssh $USER@$1 "sudo vsm-node"
    fi
}

function install_agent() {
    check_manifest $1
    set_repo $1
    ssh $USER@$1 "sudo apt-get install -y vsm vsm-deploy"
    ssh $USER@$1 "sudo preinstall"

    setup_remote_agent $1
}

#-------------------------------------------------------------------------------
#            start to install
#-------------------------------------------------------------------------------

if [[ $IS_PREPARE == False ]] && [[ $IS_CONTROLLER_INSTALL == False ]] \
    && [[ $IS_AGENT_INSTALL == False ]]; then
    prepare
    install_controller
    TOKEN=`ssh $USER@$controller_ip "sudo agent-token"`
    for ip in $storage_ip_list; do
        install_agent $ip
    done
else
    if [[ $IS_PREPARE == True ]]; then
        prepare
    fi
    if [[ $IS_CONTROLLER_INSTALL == True ]]; then
        install_controller
    fi
    if [[ $IS_AGENT_INSTALL == True ]]; then
        TOKEN=`ssh $USER@$controller_ip "sudo agent-token"`
        AGENT_IP_LIST=${NEW_AGENT_IPS//,/ }
        for ip in $AGENT_IP_LIST; do
            install_agent $ip
        done
    fi
fi

#-------------------------------------------------------------------------------
#            finish auto deploy
#-------------------------------------------------------------------------------

echo "Finished."

set +o xtrace


# change_log
# Feb 12 2015 Zhu Boxiang <boxiangx.zhu@intel.com> - 2015.2.12-1
# Initial release
# 
#
# 