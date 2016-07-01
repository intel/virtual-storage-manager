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

if [[ -z $MANIFEST_PATH ]]; then
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
    if [[ $ip == $CONTROLLER_IP ]]; then
        IS_CONTROLLER=1
    fi
done

if [[ $HOSTNAME == $CONTROLLER_IP ]]; then
    IS_CONTROLLER=1
fi

if [[ $IS_CONTROLLER -eq 0 ]]; then
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
        eval $i || :
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

function make_me_super() {              # make_me_super <user> <node>
    local user="$1"
    local node="$2"
    MKMESUPER="$user ALL=(ALL) NOPASSWD: ALL"
    if [[ $IS_CONTROLLER -eq 1 && $node == $CONTROLLER_IP ]]; then
        if ! $SUDO -n true; then
            $SUDO echo '$MKMESUPER' | $SUDO tee /etc/sudoers.d/$user
            $SUDO chmod 0440 /etc/sudoers.d/$user
        fi
    else
        $SSH $user@$node "bash -x -s" <<EOF
if ! $SUDO -n true; then
    $SUDO echo '$MKMESUPER' | $SUDO tee /etc/sudoers.d/$user
    $SUDO chmod 0440 /etc/sudoers.d/$user
fi
exit 0
EOF
    fi
}

function check_vsm_package() {
    if [[ ! -d vsmrepo ]]; then
        echo "[Error]: You must have the vsmrepo folder; please check and try again."
        exit 1
    fi
    cd vsmrepo
    IS_PYTHON_VSMCLIENT=`ls|grep python-vsmclient.*.deb|wc -l`
    IS_VSM=`ls|grep -v python-vsmclient|grep -v vsm-dashboard|grep -v vsm-deploy|grep vsm|wc -l`
    IS_VSM_DASHBOARD=`ls|grep vsm-dashboard.*.deb|wc -l`
    IS_VSM_DEPLOY=`ls|grep vsm-deploy.*.deb|wc -l`
    if [[ $IS_PYTHON_VSMCLIENT -gt 0 ]] && [[ $IS_VSM -gt 0 ]] &&\
        [[ $IS_VSM_DASHBOARD -gt 0 ]] && [[ $IS_VSM_DEPLOY -gt 0 ]]; then
        echo "[Info]: The vsm packages have already been prepared."
    else
        echo "[Error]: Please check the vsm packages and try again."
        exit 1
    fi
    cd $TOPDIR
}

function set_iptables_and_selinux() {   # set_iptables_and_selinux <node>
    local node="$1"
    $SSH $USER@$node "bash -x -s" <<EOF
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
    echo "[Info]: Preparing for Installation."
    check_vsm_package
    #set_iptables_and_selinux $CONTROLLER_IP
    download_dependencies
    prepare_repo
}

#-------------------------------------------------------------------------------
#            controller
#-------------------------------------------------------------------------------

function execute() {                    # execute "<command>" [[<user>@]<host>]
    local command="$1"
    local remote="$2"
    if [ ! -z "$remote" ]; then
        $SSH $remote "set -e; $command; true"
    else
        eval "$command; true"
    fi
}

function copy() {                       # copy [-<op1> -<op2> ...] <src> <dst> [[<user>@]<host>]
    local opt
    while [[ $1 == -* ]]; do opts+=" $1"; shift; done
    local src="$1"
    local dst="$2"
    local remote="$3"
    [[ $remote ]] && $SCP$opts $src $remote:$dst || cp$opts $src $dst
}

function set_repo() {                   # set_repo [[<user>@]<host>]
    local remote="$1"
    execute "$SUDO rm -rf /etc/apt/sources.list.d/vsm.list /etc/apt/sources.list.d/vsm-dep.list" $remote
    execute "$SUDO rm -rf /opt/vsm-dep-repo /opt/vsmrepo" $remote
    copy -r "$REPO_PATH/vsm-dep-repo" /tmp $remote
    execute "$SUDO mv /tmp/vsm-dep-repo /opt" $remote
    copy -r vsmrepo /tmp $remote
    execute "$SUDO mv /tmp/vsmrepo /opt" $remote
    execute "$SUDO rm -f /tmp/apt.conf" $remote
    execute "test -f /etc/apt/apt.conf && $SUDO mv /etc/apt/apt.conf /tmp" $remote
    execute "grep 'APT::Get::AllowUnauthenticated[[:space:]]*1' /tmp/apt.conf >/dev/null 2>&1 ||
        echo 'APT::Get::AllowUnauthenticated 1;' | $SUDO tee --append /tmp/apt.conf >/dev/null" $remote
    execute "$SUDO mv /tmp/apt.conf /etc/apt" $remote
    copy vsm.list /tmp $remote
    execute "$SUDO mv /tmp/vsm.list /etc/apt/sources.list.d" $remote
    copy vsm-dep.list /tmp $remote
    execute "$SUDO mv /tmp/vsm-dep.list /etc/apt/sources.list.d" $remote
    execute "$SUDO apt-get update" $remote
}

function check_manifest() {             # check_manifest [<node>] - no node implies controller
    local node="$1"
    local node_type
    [[ $node ]] && node_type="server" || { node_type="cluster"; node="$CONTROLLER_IP"; }
    if [[ ! -d $MANIFEST_PATH/$node ]] || [[ ! -f $MANIFEST_PATH/$node/$node_type.manifest ]]; then
        echo "[Error]: Please check the $node_type manifest for [$node] and try again."
        exit 1
    fi
}

function setup_controller() {           # setup_remote_controller [[<user>@]<host>]
    local remote="$1"
    execute "$SUDO rm -rf /etc/manifest/cluster_manifest" $remote
    copy "$MANIFEST_PATH/$CONTROLLER_IP/cluster.manifest" /tmp $remote
    execute "$SUDO mv /tmp/cluster.manifest /etc/manifest" $remote
    execute "$SUDO chown root:vsm /etc/manifest/cluster.manifest" $remote
    execute "$SUDO chmod 755 /etc/manifest/cluster.manifest" $remote
    if [[ $(execute "cluster_manifest|grep error|wc -l" $remote) -gt 0 ]]; then
        echo "[Error]: Please check the cluster.manifest and try again."
        exit 1
    else
        if [[ $OS_KEYSTONE_HOST ]] && [[ $OS_KEYSTONE_ADMIN_TOKEN ]]; then
            execute "$SUDO vsm-controller --keystone-host $OS_KEYSTONE_HOST --keystone-admin-token $OS_KEYSTONE_ADMIN_TOKEN" $remote
            execute "$SUDO service keystone status >/dev/null 2>&1 && $SUDO service keystone stop" $remote
        else
            execute "$SUDO vsm-controller" $remote
        fi
    fi
}

function install_controller() {         # install_controller
    echo "[Info]: Installing Controller."
    make_me_super $USER $CONTROLLER_IP
    check_manifest

    local remote=""
    [[ $IS_CONTROLLER -eq 0 ]] && remote="$USER@$CONTROLLER_IP"

    set_repo $remote
    execute "$SUDO apt-get install -y vsm vsm-deploy vsm-dashboard python-vsmclient diamond" $remote
    execute "$SUDO preinstall controller" $remote
    setup_controller $remote
}

#-------------------------------------------------------------------------------
#            agent
#-------------------------------------------------------------------------------

function kill_diamond() {               # kill_diamond <node>
    local node="$1"
    cat <<"EOF" >kill_diamond.sh
#!/bin/bash
diamond_pid=`ps -ef|grep diamond|grep -v grep|grep -v bash|grep -v kill_diamond|awk -F " " '{print $2}'`
for pid in $diamond_pid; do
    sudo -E kill -9 $pid
done
exit 0
EOF
    $SCP kill_diamond.sh $USER@$node:/tmp
    $SSH $USER@$node "bash -x -s" <<EOF
$SUDO chmod 755 /tmp/kill_diamond.sh
cd /tmp
./kill_diamond.sh
$SUDO rm -rf kill_diamond
exit 0
EOF
}

function install_setup_diamond() {      # install_setup_diamond <node>
    local node="$1"
#    kill_diamond $node
    $SSH $USER@$node "$SUDO apt-get install -y diamond"
    DEPLOYRC_FILE="/etc/vsmdeploy/deployrc"
    if [[ $IS_CONTROLLER -eq 0 ]]; then
        $SCP $USER@$CONTROLLER_IP:$DEPLOYRC_FILE /tmp
        source /tmp/deployrc
    else
        source $DEPLOYRC_FILE
    fi

    #local VSMMYSQL_FILE_PATH=`$SSH $USER@$node "$SUDO find / -name vsmmysql.py|grep vsm/diamond"`
    #local HANDLER_PATH=`$SSH $USER@$node "$SUDO find / -name handler|grep python"`
    #local DIAMOND_CONFIG_PATH=`$SSH $USER@$node "$SUDO find / -name diamond|grep /etc/diamond"`

    PY_VER=`python -V 2>&1 |cut -d' ' -f2 |cut -d. -f1,2`
    echo "Python version: $PY_VER"

    local VSMMYSQL_FILE_PATH="/usr/local/lib/python${PY_VER}/dist-packages/vsm/diamond/handlers/vsmmysql.py"
    local HANDLER_PATH="/usr/lib/pymodules/python${PY_VER}/diamond/handler"
    local DIAMOND_CONFIG_PATH="/etc/diamond"

    $SSH $USER@$node "bash -x -s" <<EOF
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

function setup_remote_agent() {         # setup_remote_agent <node>
    local node="$1"
    # update /etc/hosts
    #update_hosts $node
    $SSH $USER@$node "$SUDO rm -rf /etc/manifest/server.manifest"
    #$SUDO sed -i "s/token-tenant/$TOKEN/g" $MANIFEST_PATH/$node/server.manifest
    #old_str=`cat $MANIFEST_PATH/$node/server.manifest| grep ".*-.*" | grep -v by | grep -v "\["`
    #$SUDO sed -i "s/$old_str/$TOKEN/g" $MANIFEST_PATH/$node/server.manifest
    TOKEN=`cat ./.token`
    $SUDO sed -i "/^\[auth_key\]$/,/^\[.*\]/ s/^.*-.*$/$TOKEN/" $MANIFEST_PATH/$node/server.manifest
    $SCP $MANIFEST_PATH/$node/server.manifest $USER@$node:/tmp
    $SSH $USER@$node "$SUDO mv /tmp/server.manifest /etc/manifest"
    $SSH $USER@$node "$SUDO chown root:vsm /etc/manifest/server.manifest; $SUDO chmod 755 /etc/manifest/server.manifest"
    is_server_manifest_error=`$SSH $USER@$node "unset http_proxy;server_manifest" |grep ERROR|wc -l`
    if [ $is_server_manifest_error -gt 0 ]; then
        echo "[Warning]: The server.manifest on [$node] is wrong; failed to setup agent on [$node] storage node."
    else
        $SSH $USER@$node "unset http_proxy;$SUDO vsm-node"
    fi
}

function install_agent() {              # install_agent <node>
    local node="$1"
    echo "[Info]: Installing Agent on [$node]."
    make_me_super $USER $node
    generate_token
    check_manifest $node
    set_repo $USER@$node
    $SSH $USER@$node "$SUDO apt-get install -y vsm vsm-deploy"
    $SSH $USER@$node "$SUDO preinstall agent"
    setup_remote_agent $node
    install_setup_diamond $node
}

function generate_token() {
    TOKEN=`$SSH $USER@$CONTROLLER_IP "unset http_proxy; agent-token $OS_TENANT_NAME $OS_USERNAME $OS_PASSWORD $OS_KEYSTONE_HOST" |tr -d '\r'`
    echo -n $TOKEN >./.token
}

function update_hosts() {               # update_hosts <node>
    local node="$1"
    cp /etc/hosts ./.hosts
    hostname=`$SSH $USER@$node "hostname" |tr -d '\r'`
    echo "$node    $hostname" >>./.hosts
    cp ./.hosts /etc/hosts
}

function sync_hosts() {                 # sync_hosts <node>
    local node="$1"
    $SCP /etc/hosts $USER@$node:~/.hosts
    $SSH $USER@$node "$SUDO mv ~/.hosts /etc/hosts"
}

#-------------------------------------------------------------------------------
#            start to install
#-------------------------------------------------------------------------------

exit_code=0

# if --prepare option specified OR no options specified
if [[ "${IS_PREPARE}" == True ]]; then
    set +e
    ( prepare )
    prep_error="$?"
    set -e
    set +o xtrace
    if [[ "${prep_error}" -ne 0 ]]; then
        echo "[Error]: Prepare stage failed with error: ${prep_error}."
        exit "${prep_error}"
    fi
    set -o xtrace
fi

# if --controller option specified OR no options specified
if [[ "${IS_CONTROLLER_INSTALL}" == True ]]; then
    set +e
    ( install_controller )
    ctrl_error="$?"
    set -e
    set +o xtrace
    if [[ "${ctrl_error}" -ne 0 ]]; then
        echo "[Error]: Controller installation failed with error: $ctrl_error."
        exit "${ctrl_error}"
    fi
    set -o xtrace
fi

# if --agent option specified OR no options specified
if [[ "${IS_AGENT_INSTALL}" == True ]]; then
    declare -A pids
    declare -A tf_list
    echo "[Info]: Starting Async Agent Installation on [${AGENT_IPS}]."
    for ip_or_hostname in ${AGENT_IPS}; do
        tf="$(mktemp)"
        tf_list[${ip_or_hostname}]="${tf}"
        ( install_agent "${ip_or_hostname}" >${tf} 2>&1 ) &
        pids[${ip_or_hostname}]="$!"
    done

    # wait for agents to complete installing in background
    declare -A errors
    for ip_or_hostname in ${AGENT_IPS}; do
        set +e
        wait "${pids[${ip_or_hostname}]}"
        errors[${ip_or_hostname}]="$?"
        set -e
        if [[ "${errors[${ip_or_hostname}]}" -ne 0 ]]; then
            exit_code=1
        fi
    done

    # cat each agent log to the screen in startup order
    # capture the log errors in case of failure
    for ip_or_hostname in ${AGENT_IPS}; do
        cat "${tf_list[${ip_or_hostname}]}"
    done

    # sync up /etc/hosts to agents
    for ip_or_hostname in ${AGENT_IPS}; do
        echo "sync /etc/hosts to agents"
        #sync_hosts "${ip_or_hostname}"
    done

    if [[ "${IS_CONTROLLER_INSTALL}" == False ]]; then
        # sync up /etc/hosts to controller
        echo "sync /etc/hosts to controller"
        #sync_hosts "${CONTROLLER_IP}"
    fi

    # print last 10 lines of each failing agent's log OR print SUCCESS
    set +o xtrace
    if [[ "${exit_code}" -ne 0 ]]; then
        echo "[Error]: One or more agent installations failed."
        echo "[Error]: Displaying the last 10 lines of failed agent output:"
        for ip_or_hostname in ${AGENT_IPS}; do
            if [[ "${errors[${ip_or_hostname}]}" -ne 0 ]]; then
                echo "[Error]: Agent [${ip_or_hostname}] failed:"
                echo "..."
                tail -n 10 "${tf_list[${ip_or_hostname}]}"
            fi
        done
    fi
    set -o xtrace

    # delete all temporary agent logs
    for ip_or_hostname in ${AGENT_IPS}; do
        rm -f "${tf_list[${ip_or_hostname}]}"
    done
fi

#-------------------------------------------------------------------------------
#            finish auto deploy
#-------------------------------------------------------------------------------

set +o xtrace

echo "[Info]: Finished - exit code: ${exit_code}."

exit "${exit_code}"
