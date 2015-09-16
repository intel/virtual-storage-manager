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
  --key [key file] | -k [key file]
    The key file required for ssh/scp connection at the environment
  where certificate based authentication is enabled.
  --user | -u
    The user will be used to connect remote nodes to deploy vsm.
  --prepare
    Preparing to install vsm. Checking vsm packages, downloading
  the dependencies and setting the repository.
  --controller [ip or hostname]
    Installing the controller node only.
  --agent [ip,ip or hostname]
    Install the agent node(s), like: --agent ip,ip or hostname with no blank.
  --check-dependence-package
    Check the dependence package if provided the dependence repo.
EOF
    exit 0
}

MANIFEST_PATH=""
REPO_PATH="vsm-dep-repo"
DEPENDENCE_BRANCH="master"
USER=`whoami`
SSH='ssh -t'
SCP='scp'
SUDO='sudo -E'
IS_PREPARE=False
IS_CONTROLLER_INSTALL=False
IS_AGENT_INSTALL=False
NEW_CONTROLLER_ADDRESS=""
NEW_AGENT_IPS=""
IS_CHECK_DEPENDENCE_PACKAGE=False

while [ $# -gt 0 ]; do
  case "$1" in
    -h| --help) usage ;;
    -m| --manifest) shift; MANIFEST_PATH=$1 ;;
    -r| --repo-path) shift; REPO_PATH=$1 ;;
    -v| --version) shift; DEPENDENCE_BRANCH=$1 ;;
    -u| --user) shift; USER=$1 ;;
    -k| --key) shift; keyfile=$1; export SSH='ssh -i $keyfile'; export SCP='scp -i $keyfile' ;;
    --prepare) IS_PREPARE=True ;;
    --controller) shift; IS_CONTROLLER_INSTALL=True; NEW_CONTROLLER_ADDRESS=$1 ;;
    --agent) shift; IS_AGENT_INSTALL=True; NEW_AGENT_IPS=$1 ;;
    --check-dependence-package) shift; IS_CHECK_DEPENDENCE_PACKAGE=True ;;
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

source $TOPDIR/installrc

if [ -z $MANIFEST_PATH ]; then
    MANIFEST_PATH="manifest"
fi

if [[ $NEW_CONTROLLER_ADDRESS != "" ]]; then
    CONTROLLER_ADDRESS=$NEW_CONTROLLER_ADDRESS
fi

function _make_me_super() { # _make_me_super <user> <node>
    MKMESUPER="$1 ALL=(ALL) NOPASSWD: ALL"
    $SSH $USER@$2 "$SUDO echo '$MKMESUPER' | $SUDO tee /etc/sudoers.d/$1; $SUDO chmod 0440 /etc/sudoers.d/$1"
}

# enable no-password sudo
_make_me_super $USER $CONTROLLER_ADDRESS

for node in $AGENT_ADDRESS_LIST; do
    _make_me_super $USER $node
done

IS_CONTROLLER=0
for ip in $HOSTIP; do
    if [ $ip == $CONTROLLER_ADDRESS ]; then
        IS_CONTROLLER=1
    fi
done

if [[ $HOSTNAME == $CONTROLLER_ADDRESS ]]; then
    IS_CONTROLLER=1
fi

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
    $SSH $USER@$1 "service iptables stop"
    $SSH $USER@$1 "chkconfig iptables off"
    $SSH $USER@$1 "sed -i \"s/SELINUX=enforcing/SELINUX=disabled/g\" /etc/selinux/config"
    $SSH $USER@$1 "setenforce 0"
}

function download_dependencies() {
    if [[ ! -d $REPO_PATH ]]; then
        mkdir -p $REPO_PATH
        cd $REPO_PATH
        for i in `cat $TOPDIR/debs.lst`; do
            wget https://github.com/01org/vsm-dependencies/raw/$DEPENDENCE_BRANCH/ubuntu14/$i
        done
        cd $TOPDIR
    elif [[ -d $REPO_PATH ]] && [[ $IS_CHECK_DEPENDENCE_PACKAGE == True ]]; then
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
        $SUDO rm -rf *.deb.*
        cd $TOPDIR
    fi
}

function prepare_repo() {
    $SUDO apt-get update
    IS_DPKG_DEV=`dpkg -s dpkg-dev|grep "install ok installed"|wc -l`
    if [[ $IS_DPKG_DEV -eq 0 ]]; then
        $SUDO apt-get install -y dpkg-dev
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

function set_remote_repo() {
    $SSH $USER@$1 "$SUDO rm -rf /etc/apt/sources.list.d/vsm.list /etc/apt/sources.list.d/vsm-dep.list; \
        $SUDO rm -rf /opt/vsm-dep-repo /opt/vsmrepo"
    $SCP -r $REPO_PATH/vsm-dep-repo $USER@$1:/tmp
    $SSH $USER@$1 "$SUDO mv /tmp/vsm-dep-repo /opt"
    $SCP -r vsmrepo $USER@$1:/tmp
    $SSH $USER@$1 "$SUDO mv /tmp/vsmrepo /opt"
    $SSH $USER@$1 "if [[ -f /etc/apt/apt.conf ]]; then $SUDO mv /etc/apt/apt.conf /tmp; $SUDO chown $USER /tmp/apt.conf; \
        $SUDO echo \"APT::Get::AllowUnauthenticated 1 ;\" >> /tmp/apt.conf; $SUDO chown root /tmp/apt.conf; $SUDO mv /tmp/apt.conf /etc/apt; \
        else touch /tmp/apt.conf; echo \"APT::Get::AllowUnauthenticated 1 ;\" >> /tmp/apt.conf; \
        $SUDO mv /tmp/apt.conf /etc/apt; fi"
#    $SCP apt.conf $USER@$1:/etc/apt
    $SCP vsm.list $USER@$1:/tmp
    $SSH $USER@$1 "$SUDO mv /tmp/vsm.list /etc/apt/sources.list.d"
    $SCP vsm-dep.list $USER@$1:/tmp
    $SSH $USER@$1 "$SUDO mv /tmp/vsm-dep.list /etc/apt/sources.list.d"
    $SSH $USER@$1 "$SUDO apt-get update"
}

function set_local_repo() {
    $SUDO rm -rf /etc/apt/sources.list.d/vsm.list /etc/apt/sources.list.d/vsm-dep.list
    $SUDO rm -rf /opt/vsm-dep-repo /opt/vsmrepo
    $SUDO cp -r $REPO_PATH/vsm-dep-repo /opt
    $SUDO cp -r vsmrepo /opt
    if [[ -f /etc/apt/apt.conf ]]; then
        $SUDO mv /etc/apt/apt.conf /tmp
        $SUDO chown $USER /tmp/apt.conf
        $SUDO echo "APT::Get::AllowUnauthenticated 1 ;" >> /tmp/apt.conf
        $SUDO chown root /tmp/apt.conf
        $SUDO mv /tmp/apt.conf /etc/apt
    else
        touch /tmp/apt.conf
        echo "APT::Get::AllowUnauthenticated 1 ;" >> /tmp/apt.conf
        $SUDO mv /tmp/apt.conf /etc/apt
    fi
    $SUDO cp vsm.list /etc/apt/sources.list.d
    $SUDO cp vsm-dep.list /etc/apt/sources.list.d
    $SUDO apt-get update
}

function check_manifest() {
    if [[ $1 == $CONTROLLER_ADDRESS ]]; then
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
    $SSH $USER@$CONTROLLER_ADDRESS "$SUDO rm -rf /etc/manifest/cluster_manifest"
    $SCP $MANIFEST_PATH/$CONTROLLER_ADDRESS/cluster.manifest $USER@$CONTROLLER_ADDRESS:/tmp
    $SSH $USER@$CONTROLLER_ADDRESS "$SUDO mv /tmp/cluster.manifest /etc/manifest"
    $SSH $USER@$CONTROLLER_ADDRESS "$SUDO chown root:vsm /etc/manifest/cluster.manifest; $SUDO chmod 755 /etc/manifest/cluster.manifest"
    is_cluster_manifest_error=`$SSH $USER@$CONTROLLER_ADDRESS "cluster_manifest|grep error|wc -l"`
    if [ $is_cluster_manifest_error -gt 0 ]; then
        echo "please check the cluster.manifest, then try again"
        exit 1
    else
        if [[ $OS_KEYSTONE_HOST ]] && [[ $OS_KEYSTONE_ADMIN_TOKEN ]]; then
            $SSH $USER@$CONTROLLER_ADDRESS "$SUDO vsm-controller --keystone-host $OS_KEYSTONE_HOST --keystone-admin-token $OS_KEYSTONE_ADMIN_TOKEN"
            $SSH $USER@$CONTROLLER_ADDRESS "if [[ `$SUDO service keystone status|grep running|wc -l` == 1 ]]; then $SUDO service keystone stop; fi"
        else
            $SSH $USER@$CONTROLLER_ADDRESS "$SUDO vsm-controller"
        fi
    fi
}

function install_controller() {
#    _make_me_super $USER $CONTROLLER_ADDRESS
    check_manifest $CONTROLLER_ADDRESS

    if [[ $IS_CONTROLLER -eq 0 ]]; then
        set_remote_repo $CONTROLLER_ADDRESS
        $SSH $USER@$CONTROLLER_ADDRESS "$SUDO apt-get install -y vsm vsm-deploy vsm-dashboard python-vsmclient diamond"
        $SSH $USER@$CONTROLLER_ADDRESS "$SUDO preinstall controller"
        setup_remote_controller
        $SCP $USER@$CONTROLLER_ADDRESS:/var/cache/apt/archives/*.deb $REPO_PATH/vsm-dep-repo
        cd $REPO_PATH
        dpkg-scanpackages vsm-dep-repo | gzip > vsm-dep-repo/Packages.gz
        cd $TOPDIR
    else
        set_local_repo
        $SUDO apt-get install -y vsm vsm-deploy vsm-dashboard python-vsmclient diamond
        $SUDO preinstall controller
        $SUDO rm -rf /etc/manifest/cluster.manifest
        $SUDO cp $MANIFEST_PATH/$CONTROLLER_ADDRESS/cluster.manifest /etc/manifest
        $SUDO chown root:vsm /etc/manifest/cluster.manifest
        $SUDO chmod 755 /etc/manifest/cluster.manifest
        if [ `cluster_manifest|grep error|wc -l` -gt 0 ]; then
            echo "please check the cluster.manifest, then try again"
            exit 1
        else
            if [[ $OS_KEYSTONE_HOST ]] && [[ $OS_KEYSTONE_ADMIN_TOKEN ]]; then
                $SUDO vsm-controller --keystone-host $OS_KEYSTONE_HOST --keystone-admin-token $OS_KEYSTONE_ADMIN_TOKEN
                if [[ `$SUDO service keystone status|grep running|wc -l` == 1 ]]; then $SUDO service keystone stop; fi
            else
                $SUDO vsm-controller
            fi
        fi
        cp /var/cache/apt/archives/*.deb $REPO_PATH/vsm-dep-repo
        cd $REPO_PATH
        dpkg-scanpackages vsm-dep-repo | gzip > vsm-dep-repo/Packages.gz
        cd $TOPDIR
    fi
    
#    generate_token
}

#-------------------------------------------------------------------------------
#            agent
#-------------------------------------------------------------------------------

function kill_diamond() {
    cat <<"EOF" >kill_diamond.sh
#!/bin/bash
diamond_pid=`ps -ef|grep diamond|grep -v grep|grep -v bash|awk -F " " '{print $2}'`
for pid in $diamond_pid; do
    sudo -E kill -9 $pid
done
EOF
    $SCP kill_diamond.sh $USER@$1:/tmp
    $SSH $USER@$1 "$SUDO chmod 755 /tmp/kill_diamond.sh;" \
    "cd /tmp;" \
    "./kill_diamond.sh;" \
    "$SUDO rm -rf kill_diamond"
}

function install_setup_diamond() {
    kill_diamond $1
    $SSH $USER@$1 "$SUDO apt-get install -y diamond"
    DEPLOYRC_FILE="/etc/vsmdeploy/deployrc"
    if [[ $IS_CONTROLLER -eq 0 ]]; then
        $SCP $USER@$CONTROLLER_ADDRESS:$DEPLOYRC_FILE /tmp
        source /tmp/deployrc
    else
        source $DEPLOYRC_FILE
    fi
    #VSMMYSQL_FILE_PATH=`$SSH $USER@$1 "$SUDO find / -name vsmmysql.py|grep vsm/diamond"`
    #HANDLER_PATH=`$SSH $USER@$1 "$SUDO find / -name handler|grep python"`
    #DIAMOND_CONFIG_PATH=`$SSH $USER@$1 "$SUDO find / -name diamond|grep /etc/diamond"`
    PY_VER=`python -V 2>&1 |cut -d' ' -f2 |cut -d. -f1,2`
    echo "Python version: $PY_VER"
    VSMMYSQL_FILE_PATH="/usr/local/lib/python${PY_VER}/dist-packages/vsm/diamond/handlers/vsmmysql.py"
    HANDLER_PATH="/usr/lib/pymodules/python${PY_VER}/diamond/handler"
    DIAMOND_CONFIG_PATH="/etc/diamond"

    $SSH $USER@$1 "$SUDO cp $DIAMOND_CONFIG_PATH/diamond.conf.example $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO cp $VSMMYSQL_FILE_PATH $HANDLER_PATH;" \
    "$SUDO sed -i \"s/MySQLHandler/VSMMySQLHandler/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/^handlers = *.*ArchiveHandler$/handlers =  diamond.handler.vsmmysql.VSMMySQLHandler/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/host = graphite/host = 127.0.0.1/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/^hostname*=*.*/hostname    = $CONTROLLER_ADDRESS/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/username    = root/username    = vsm/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/password*=*.*/password    = $MYSQL_VSM_PASSWORD/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/database    = diamond/database    = vsm/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\# INT UNSIGNED NOT NULL/a\# VARCHAR(255) NOT NULL\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\# INT UNSIGNED NOT NULL/acol_instance = instance\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\# INT UNSIGNED NOT NULL/a\# VARCHAR(255) NOT NULL\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\# INT UNSIGNED NOT NULL/acol_hostname    = hostname\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\# And any other config settings from GraphiteHandler are valid here/i\[\[SignalfxHandler\]\]\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\# And any other config settings from GraphiteHandler are valid here/iauth_token = abcdefghijklmnopqrstuvwxyz\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/\# interval = 300/interval = 20/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/enabled = True/#enabled = True/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/\[\[DiskSpaceCollector\]\]/\#\[\[DiskSpaceCollector\]\]/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/\[\[DiskUsageCollector\]\]/\#\[\[DiskUsageCollector\]\]/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/\[\[LoadAverageCollector\]\]/\#\[\[LoadAverageCollector\]\]/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/\[\[MemoryCollector\]\]/\#\[\[MemoryCollector\]\]/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"s/\[\[VMStatCollector\]\]/\#\[\[VMStatCollector\]\]/g\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\[\[CPUCollector\]\]/i\[\[CephCollector\]\]\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\[\[CPUCollector\]\]/ienabled = True\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\[\[CPUCollector\]\]/i\[\[NetworkCollector\]\]\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\[\[CPUCollector\]\]/ienabled = True\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO sed -i \"/\[\[CPUCollector\]\]/aenabled = True\" $DIAMOND_CONFIG_PATH/diamond.conf;" \
    "$SUDO diamond"
}

function setup_remote_agent() {
#    _make_me_super $USER $1
    # update /etc/hosts
    #update_hosts $1 
    $SSH $USER@$1 "$SUDO rm -rf /etc/manifest/server.manifest"
    #$SUDO sed -i "s/token-tenant/$TOKEN/g" $MANIFEST_PATH/$1/server.manifest
    #old_str=`cat $MANIFEST_PATH/$1/server.manifest| grep ".*-.*" | grep -v by | grep -v "\["`
    #$SUDO sed -i "s/$old_str/$TOKEN/g" $MANIFEST_PATH/$1/server.manifest
    TOKEN=`cat ./.token`
    $SUDO sed -i "/^\[auth_key\]$/,/^\[.*\]/ s/^.*-.*$/$TOKEN/" $MANIFEST_PATH/$1/server.manifest
    $SCP $MANIFEST_PATH/$1/server.manifest $USER@$1:/tmp
    $SSH $USER@$1 "$SUDO mv /tmp/server.manifest /etc/manifest"
    $SSH $USER@$1 "$SUDO chown root:vsm /etc/manifest/server.manifest; $SUDO chmod 755 /etc/manifest/server.manifest"
    is_server_manifest_error=`$SSH $USER@$1 "server_manifest|grep ERROR|wc -l"`
    if [ $is_server_manifest_error -gt 0 ]; then
        echo "[warning]: The server.manifest in $1 is wrong, so fail to setup in $1 storage node"
    else
        $SSH $USER@$1 "$SUDO vsm-node"
    fi
}

function install_agent() {
    $SSH $USER@$1 "if [[ -f /etc/apt/sources.list ]]; then $SUDO mv /etc/apt/sources.list /etc/apt/sources.list.bak; fi"
    check_manifest $1
    set_remote_repo $1
    $SSH $USER@$1 "$SUDO apt-get install -y vsm vsm-deploy"
    $SSH $USER@$1 "$SUDO preinstall agent"
#    $SSH $USER@$1 "if [ -r /etc/init/ceph-all.conf ] && [ ! -e /etc/init/ceph.conf ]; then sudo ln -s /etc/init/ceph-all.conf /etc/init/ceph.conf; sudo initctl reload-configuration; fi"

    setup_remote_agent $1
    install_setup_diamond $1
    $SSH $USER@$1 "if [[ -f /etc/apt/sources.list.bak ]]; then $SUDO mv /etc/apt/sources.list.bak /etc/apt/sources.list; fi"
}

function generate_token() {
    TOKEN=`$SSH $USER@$CONTROLLER_ADDRESS "unset http_proxy; agent-token \
$OS_TENANT_NAME $OS_USERNAME $OS_PASSWORD $OS_KEYSTONE_HOST" |tr -d '\r'`
    echo -n $TOKEN >./.token
}

function update_hosts() {
    cp /etc/hosts ./.hosts
    hostname=`$SSH $USER@$1 "hostname" |tr -d '\r'`
    echo "$1    $hostname" >>./.hosts
    cp ./.hosts /etc/hosts
}

function sync_hosts() {
    $SCP /etc/hosts $USER@$1:~/.hosts
    $SSH $USER@$1 "$SUDO mv ~/.hosts /etc/hosts"
}

#-------------------------------------------------------------------------------
#            start to install
#-------------------------------------------------------------------------------

if [[ $IS_PREPARE == False ]] && [[ $IS_CONTROLLER_INSTALL == False ]] \
    && [[ $IS_AGENT_INSTALL == False ]]; then
    prepare
    install_controller
    generate_token
#    if [[ $IS_CONTROLLER -eq 0 ]]; then
#        TOKEN=`$SSH $USER@$CONTROLLER_ADDRESS "unset http_proxy; agent-token \
# $OS_TENANT_NAME $OS_USERNAME $OS_PASSWORD $OS_KEYSTONE_HOST"`
#	echo -n $TOKEN >./.token
#    else
#        TOKEN=`unset http_proxy; agent-token $OS_TENANT_NAME $OS_USERNAME $OS_PASSWORD $OS_KEYSTONE_HOST`
#	echo -n $TOKEN >./.token
#    fi
    for ip_or_hostname in $AGENT_ADDRESS_LIST; do
        install_agent $ip_or_hostname
    done
else
    if [[ $IS_PREPARE == True ]]; then
        prepare
    fi
    if [[ $IS_CONTROLLER_INSTALL == True ]]; then
        install_controller
    fi
    if [[ $IS_AGENT_INSTALL == True ]]; then
        generate_token
#        if [[ $IS_CONTROLLER -eq 0 ]]; then
#            TOKEN=`$SSH $USER@$CONTROLLER_ADDRESS "unset http_proxy; agent-token \
# $OS_TENANT_NAME $OS_USERNAME $OS_PASSWORD $OS_KEYSTONE_HOST"`
#	    echo -n $TOKEN >./.token
#        else
#            TOKEN=`unset http_proxy; agent-token $OS_TENANT_NAME $OS_USERNAME $OS_PASSWORD $OS_KEYSTONE_HOST`
#	    echo -n $TOKEN >./.token
#        fi

        AGENT_IP_LIST=${NEW_AGENT_IPS//,/ }
        for ip_or_hostname in $AGENT_IP_LIST; do
            install_agent $ip_or_hostname
        done
	
	# sync up /etc/hosts
	if [[ $IS_CONTROLLER_INSTALL == False ]]; then
       	    echo "sync /etc/hosts to controller"
	    #sync_hosts $CONTROLLER_ADDRESS 
	fi

	for ip_or_hostname in $AGENT_IP_LIST; do
	    echo "sync /etc/hosts to agents"
	    #sync_hosts $ip_or_hostname
	done
    fi
fi

#-------------------------------------------------------------------------------
#            finish auto deploy
#-------------------------------------------------------------------------------

echo "Finished."

set +o xtrace

