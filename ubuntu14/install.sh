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
    This tool can help you deploy the vsm envirement automatically.
    Please run the command like: bash +x install.sh or ./install.sh

    Before auto-deploying VSM, please be sure that you have set up
    the manifests, and that you've modified them appropriately.
    For example:
        manifest
            192.168.100.100
                cluster.manifest
            192.168.100.101
                server.manifest

Options:
  --help | -h
    Print usage information.
  --manifest [manifest directory] | -m [manifest directory]
    The directory in which to find server and cluster manifests.
  --repo-path [dependencies path]
    The path of package dependencies.
  --version [master] | -v [master]
    The version of vsm dependences to download(Default=master).
  --key [key file] | -k [key file]
    The key file required for ssh/scp connection at the environment
    where certificate based authentication is enabled.
  --user | -u
    The user to be used when connecting to remote nodes to deploy vsm.
  --prepare
    Run prepare stage only. Check vsm packages, download
    package dependencies and set up the package repository.
  --controller [ip or hostname]
    Run controller installation only.
  --agent [ip,ip or hostname]
    Run agent installation only - e.g., --agent ip,ip or hostname with no blank.
  --check-dependence-package
    Check the dependent packages, assuming the dependence repo exists.
EOF
    exit 0
}

#-------------------------------------------------------------------------------
#            command-line parsing
#-------------------------------------------------------------------------------

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
CONTROLLER_IP=""
AGENT_IPS=""
IS_CHECK_DEPENDENCE_PACKAGE=False

while [ $# -gt 0 ]; do
  case "$1" in
    -h| --help) usage ;;
    -m| --manifest) shift; MANIFEST_PATH=$1 ;;
    -r| --repo-path) shift; REPO_PATH=$1 ;;
    -v| --version) shift; DEPENDENCE_BRANCH=$1 ;;
    -u| --user) shift; USER=$1 ;;
    -k| --key) shift; keyfile=$1; export SSH="ssh -i $keyfile -t "; export SCP="scp -i $keyfile" ;;
    --prepare) IS_PREPARE=True ;;
    --controller) shift; IS_CONTROLLER_INSTALL=True; CONTROLLER_IP=$1 ;;
    --agent) shift; IS_AGENT_INSTALL=True; AGENT_IPS=${1//,/ } ;;
    --check-dependence-package) shift; IS_CHECK_DEPENDENCE_PACKAGE=True ;;
    *) shift ;;
  esac
  shift
done

set -e
set -o xtrace

TOPDIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null; mkdir -p $TEMP;

HOSTNAME=`hostname`
HOSTIP=`hostname -I`

source $TOPDIR/installrc

if [ -z $MANIFEST_PATH ]; then
    MANIFEST_PATH="manifest"
fi

# if no specific installation type was requested, turn them all on
if [[ $IS_PREPARE == False ]] && [[ $IS_CONTROLLER_INSTALL == False ]]\
    && [[ $IS_AGENT_INSTALL == False ]]; then
    IS_PREPARE=True
    IS_CONTROLLER_INSTALL=True
    IS_AGENT_INSTALL=True
fi

if [[ $CONTROLLER_IP == "" ]]; then
    CONTROLLER_IP=$CONTROLLER_ADDRESS
fi

if [[ $AGENT_IPS == "" ]]; then
    AGENT_IPS=$AGENT_ADDRESS_LIST
fi

IS_CONTROLLER=0
for ip in $HOSTIP; do
    if [ $ip == $CONTROLLER_IP ]; then
        IS_CONTROLLER=1
    fi
done

if [[ $HOSTNAME == $CONTROLLER_IP ]]; then
    IS_CONTROLLER=1
fi

if [ $IS_CONTROLLER -eq 0 ]; then
    echo "[Info]: Running installer on non-cluster server."
else
    echo "[Info]: Running installer on the controller server."
fi

#-------------------------------------------------------------------------------
#            exit handling
#-------------------------------------------------------------------------------

declare -a on_exit_items
function on_exit()
{
    for i in "${on_exit_items[@]}"; do
        eval $i
    done
}

function add_on_exit()
{
    local n=${#on_exit_items[*]}
    on_exit_items[$n]="$*"
    if [[ $n -eq 0 ]]; then
        trap on_exit EXIT
    fi
}

#-------------------------------------------------------------------------------
#            prepare
#-------------------------------------------------------------------------------

# make_me_super <user> <node>
function make_me_super() {
    MKMESUPER="$1 ALL=(ALL) NOPASSWD: ALL"
    if [[ $IS_CONTROLLER -eq 1 && $2 == $CONTROLLER_IP ]]; then
        if ! $SUDO -n true; then
            $SUDO echo '$MKMESUPER' | $SUDO tee /etc/sudoers.d/$1
            $SUDO chmod 0440 /etc/sudoers.d/$1
        fi
    else
        $SSH $USER@$2 "bash -x -s" <<EOF
if ! $SUDO -n true; then
    $SUDO echo '$MKMESUPER' | $SUDO tee /etc/sudoers.d/$1
    $SUDO chmod 0440 /etc/sudoers.d/$1
fi
exit 0
EOF
    fi
}

function check_vsm_package() {
    if [[ ! -d vsmrepo ]]; then
        echo "You must have the vsmrepo folder, please check and try again."
        exit 1
    fi
    cd vsmrepo
    IS_PYTHON_VSMCLIENT=`ls|grep python-vsmclient.*.deb|wc -l`
    IS_VSM=`ls|grep -v python-vsmclient|grep -v vsm-dashboard|grep -v vsm-deploy|grep vsm|wc -l`
    IS_VSM_DASHBOARD=`ls|grep vsm-dashboard.*.deb|wc -l`
    IS_VSM_DEPLOY=`ls|grep vsm-deploy.*.deb|wc -l`
    if [[ $IS_PYTHON_VSMCLIENT -gt 0 ]] && [[ $IS_VSM -gt 0 ]] &&\
        [[ $IS_VSM_DASHBOARD -gt 0 ]] && [[ $IS_VSM_DEPLOY -gt 0 ]]; then
        echo "The vsm pachages have been already prepared"
    else
        echo "please check the vsm packages, then try again"
        exit 1
    fi
    cd $TOPDIR
}

function set_iptables_and_selinux() { # set_iptables_and_selinux <node>
    $SSH $USER@$1 "bash -x -s" <<EOF
service iptables stop
chkconfig iptables off
sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config
setenforce 0
exit 0
EOF
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
            pkg_name=${i%%_*}_
            if [[ `ls |grep $pkg_name|wc -l` -eq 0 ]]; then
                wget https://github.com/01org/vsm-dependencies/raw/$DEPENDENCE_BRANCH/ubuntu14/$i
            else
                rm $pkg_name*
                wget https://github.com/01org/vsm-dependencies/raw/$DEPENDENCE_BRANCH/ubuntu14/$i
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
    $SSH $USER@$1 "bash -x -s" <<EOF
$SUDO rm -rf /etc/apt/sources.list.d/vsm.list /etc/apt/sources.list.d/vsm-dep.list
$SUDO rm -rf /opt/vsm-dep-repo /opt/vsmrepo
EOF
    $SCP -r $REPO_PATH/vsm-dep-repo $USER@$1:/tmp
    $SSH $USER@$1 "$SUDO mv /tmp/vsm-dep-repo /opt"
    $SCP -r vsmrepo $USER@$1:/tmp
    $SSH $USER@$1 "$SUDO mv /tmp/vsmrepo /opt"
    $SSH $USER@$1 "bash -x -s" <<EOF
$SUDO rm -f /tmp/apt.conf
test -f /etc/apt/apt.conf && $SUDO mv /etc/apt/apt.conf /tmp
grep "APT::Get::AllowUnauthenticated" /tmp/apt.conf >/dev/null 2>&1\
    || echo "APT::Get::AllowUnauthenticated 1 ;" | $SUDO tee --append /tmp/apt.conf >/dev/null
$SUDO mv /tmp/apt.conf /etc/apt
EOF
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
    $SUDO rm -f /tmp/apt.conf
    test -f /etc/apt/apt.conf && $SUDO mv /etc/apt/apt.conf /tmp
    grep "APT::Get::AllowUnauthenticated" /tmp/apt.conf >/dev/null 2>&1\
        || echo "APT::Get::AllowUnauthenticated 1 ;" | $SUDO tee --append /tmp/apt.conf >/dev/null
    $SUDO mv /tmp/apt.conf /etc/apt
    $SUDO cp vsm.list /etc/apt/sources.list.d
    $SUDO cp vsm-dep.list /etc/apt/sources.list.d
    $SUDO apt-get update
}

function check_manifest() {
    if [[ $1 == $CONTROLLER_IP ]]; then
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
    $SSH $USER@$CONTROLLER_IP "$SUDO rm -rf /etc/manifest/cluster_manifest"
    $SCP $MANIFEST_PATH/$CONTROLLER_IP/cluster.manifest $USER@$CONTROLLER_IP:/tmp
    $SSH $USER@$CONTROLLER_IP "$SUDO mv /tmp/cluster.manifest /etc/manifest"
    $SSH $USER@$CONTROLLER_IP "$SUDO chown root:vsm /etc/manifest/cluster.manifest; $SUDO chmod 755 /etc/manifest/cluster.manifest"
    is_cluster_manifest_error=`$SSH $USER@$CONTROLLER_IP "cluster_manifest|grep error|wc -l"`
    if [ $is_cluster_manifest_error -gt 0 ]; then
        echo "please check the cluster.manifest, then try again"
        exit 1
    else
        if [[ $OS_KEYSTONE_HOST ]] && [[ $OS_KEYSTONE_ADMIN_TOKEN ]]; then
            $SSH $USER@$CONTROLLER_IP "$SUDO vsm-controller --keystone-host $OS_KEYSTONE_HOST --keystone-admin-token $OS_KEYSTONE_ADMIN_TOKEN"
            $SSH $USER@$CONTROLLER_IP "if [[ `$SUDO service keystone status|grep running|wc -l` == 1 ]]; then $SUDO service keystone stop; fi"
        else
            $SSH $USER@$CONTROLLER_IP "$SUDO vsm-controller"
        fi
    fi
}

function install_controller() {
    make_me_super $USER $CONTROLLER_IP
    check_manifest $CONTROLLER_IP

    if [[ $IS_CONTROLLER -eq 0 ]]; then
        set_remote_repo $CONTROLLER_IP
        $SSH $USER@$CONTROLLER_IP "$SUDO apt-get install -y vsm vsm-deploy vsm-dashboard python-vsmclient diamond"
        $SSH $USER@$CONTROLLER_IP "$SUDO preinstall controller"
        setup_remote_controller
    else
        set_local_repo
        $SUDO apt-get install -y vsm vsm-deploy vsm-dashboard python-vsmclient diamond
        $SUDO preinstall controller
        $SUDO rm -rf /etc/manifest/cluster.manifest
        $SUDO cp $MANIFEST_PATH/$CONTROLLER_IP/cluster.manifest /etc/manifest
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
    fi
}

#-------------------------------------------------------------------------------
#            agent
#-------------------------------------------------------------------------------

function kill_diamond() { # kill_diamond <node>
    cat <<"EOF" >kill_diamond.sh
#!/bin/bash
diamond_pid=`ps -ef|grep diamond|grep -v grep|grep -v bash|grep -v kill_diamond|awk -F " " '{print $2}'`
for pid in $diamond_pid; do
    sudo -E kill -9 $pid
done
exit 0
EOF
    $SCP kill_diamond.sh $USER@$1:/tmp
    $SSH $USER@$1 "bash -x -s" <<EOF
$SUDO chmod 755 /tmp/kill_diamond.sh
cd /tmp
./kill_diamond.sh
$SUDO rm -rf kill_diamond
exit 0
EOF
}

function install_setup_diamond() {
#    kill_diamond $1
    $SSH $USER@$1 "$SUDO apt-get install -y diamond"
    DEPLOYRC_FILE="/etc/vsmdeploy/deployrc"
    if [[ $IS_CONTROLLER -eq 0 ]]; then
        $SCP $USER@$CONTROLLER_IP:$DEPLOYRC_FILE /tmp
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

    $SSH $USER@$1 "bash -x -s" <<EOF
$SUDO cp $DIAMOND_CONFIG_PATH/diamond.conf.example $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO cp $VSMMYSQL_FILE_PATH $HANDLER_PATH
$SUDO sed -i "s/MySQLHandler/VSMMySQLHandler/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/^handlers = *.*ArchiveHandler$/handlers =  diamond.handler.vsmmysql.VSMMySQLHandler/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/host = graphite/host = 127.0.0.1/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/^hostname*=*.*/hostname    = $CONTROLLER_IP/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/username    = root/username    = vsm/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/password*=*.*/password    = $MYSQL_VSM_PASSWORD/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/database    = diamond/database    = vsm/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\# INT UNSIGNED NOT NULL/a\# VARCHAR(255) NOT NULL" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\# INT UNSIGNED NOT NULL/acol_instance = instance" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\# INT UNSIGNED NOT NULL/a\# VARCHAR(255) NOT NULL" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\# INT UNSIGNED NOT NULL/acol_hostname    = hostname" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\# And any other config settings from GraphiteHandler are valid here/i\[\[SignalfxHandler\]\]" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\# And any other config settings from GraphiteHandler are valid here/iauth_token = abcdefghijklmnopqrstuvwxyz" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/\# interval = 300/interval = 20/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/enabled = True/#enabled = True/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/\[\[DiskSpaceCollector\]\]/\#\[\[DiskSpaceCollector\]\]/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/\[\[DiskUsageCollector\]\]/\#\[\[DiskUsageCollector\]\]/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/\[\[LoadAverageCollector\]\]/\#\[\[LoadAverageCollector\]\]/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/\[\[MemoryCollector\]\]/\#\[\[MemoryCollector\]\]/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "s/\[\[VMStatCollector\]\]/\#\[\[VMStatCollector\]\]/g" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\[\[CPUCollector\]\]/i\[\[CephCollector\]\]" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\[\[CPUCollector\]\]/ienabled = False" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\[\[CPUCollector\]\]/i\[\[NetworkCollector\]\]" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\[\[CPUCollector\]\]/ienabled = False" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO sed -i "/\[\[CPUCollector\]\]/aenabled = False" $DIAMOND_CONFIG_PATH/diamond.conf
$SUDO service diamond restart
exit 0
EOF
}

function setup_remote_agent() { # setup_remote_agent <node>
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
    is_server_manifest_error=`$SSH $USER@$1 "unset http_proxy;server_manifest" |grep ERROR|wc -l`
    if [ $is_server_manifest_error -gt 0 ]; then
        echo "[warning]: The server.manifest in $1 is wrong, so fail to setup in $1 storage node"
    else
        $SSH $USER@$1 "unset http_proxy;$SUDO vsm-node"
    fi
}

function install_agent() { # install_agent <node>
    echo "=== Install agent [$1] start."
    make_me_super $USER $1
    generate_token
    check_manifest $1
    set_remote_repo $1
    $SSH $USER@$1 "$SUDO apt-get install -y vsm vsm-deploy"
    $SSH $USER@$1 "$SUDO preinstall agent"
#    $SSH $USER@$1 "if [ -r /etc/init/ceph-all.conf ] && [ ! -e /etc/init/ceph.conf ]; then sudo ln -s /etc/init/ceph-all.conf /etc/init/ceph.conf; sudo initctl reload-configuration; fi"

    setup_remote_agent $1
    install_setup_diamond $1
    echo "=== Install agent [$1] complete."
}

function generate_token() {
    TOKEN=`$SSH $USER@$CONTROLLER_IP "unset http_proxy; agent-token $OS_TENANT_NAME $OS_USERNAME $OS_PASSWORD $OS_KEYSTONE_HOST" |tr -d '\r'`
    echo -n $TOKEN >./.token
}

function update_hosts() { # update_hosts <node>
    cp /etc/hosts ./.hosts
    hostname=`$SSH $USER@$1 "hostname" |tr -d '\r'`
    echo "$1    $hostname" >>./.hosts
    cp ./.hosts /etc/hosts
}

function sync_hosts() { # sync_hosts <node>
    $SCP /etc/hosts $USER@$1:~/.hosts
    $SSH $USER@$1 "$SUDO mv ~/.hosts /etc/hosts"
}

#-------------------------------------------------------------------------------
#            start to install
#-------------------------------------------------------------------------------

exit_code=0

# if --prepare option specified OR no options specified
if [[ $IS_PREPARE == True ]]; then
    prepare
fi

# if --controller option specified OR no options specified
if [[ $IS_CONTROLLER_INSTALL == True ]]; then
    install_controller
fi

# if --agent option specified OR no options specified
if [[ $IS_AGENT_INSTALL == True ]]; then
    pids=""
    tf_list=""
    for ip_or_hostname in $AGENT_IPS; do
        tf=$(mktemp)
        tf_list+=" ${tf}"
        echo "=== Starting asynchronous agent install [$ip_or_hostname] ..."
        ( install_agent $ip_or_hostname >${tf} 2>&1 ) &
        pids+=" $!"
    done

    # wait for agents to complete installing in background
    for p in $pids; do
        if ! wait $p; then
            exit_code=1
        fi
    done

    # cat each agent log to the screen in startup order
    for tf in ${tf_list}; do cat ${tf}; rm -f ${tf}; done

    # sync up /etc/hosts to agents
    for ip_or_hostname in $AGENT_IP_LIST; do
        echo "sync /etc/hosts to agents"
        #sync_hosts $ip_or_hostname
    done

    if [[ $IS_CONTROLLER_INSTALL == False ]]; then
        # sync up /etc/hosts to controller
        echo "sync /etc/hosts to controller"
        #sync_hosts $CONTROLLER_IP
    fi

    test ${exit_code} -ne 0 && echo "ERROR: At least one agent failed to install properly."
fi

#-------------------------------------------------------------------------------
#            finish auto deploy
#-------------------------------------------------------------------------------

echo "Finished."

set +o xtrace

exit $exit_code

