#!/bin/bash

# OS: Ubuntu 14.04
# VSM: v2.1
# upgrade.sh: v0.9

function usage() {
    cat << EOF
Usage: upgrade.sh --controller <controller> --agent <agent[,agent]>

VSM Upgrade:
    This utility upgrades VSM packages on controller and agent nodes in the ceph cluster.
    Supply the IP or Hostname of the controller and agent nodes.

Options:
    --help|-h
        Print this usage information.
    --controller|-c <controller>
        Controller node IP address or host name.
    --agent|-a <agent[,agent]>
        Agent node IP addresses or host names.
    --version|-v
        The version of this script.
EOF
    exit 0
}

SSH="ssh -t"
SCP="scp -r"
SUDO="sudo -E"
CONTROLLER_ADDRESS=""
AGENT_ADDRESS_LIST=""
REPO="vsmrepo"
VERSION="version 0.9"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help) usage ;;
        -c|--controller) shift; CONTROLLER_ADDRESS=$1 ;;
        -a|--agent) shift; AGENT_ADDRESS_LIST=$1 ;;
        -v|--version) echo $VERSION; exit 0 ;;
        *) echo "[Error]: Invalid parameters $1"; exit 1 ;;
    esac
    shift
done

set -e
set -o xtrace

#TOPDIR=$(cd $(dirname "$0") && pwd)

function upgrade_controller() {          # upgrade_controller <controller-address> <controller-is-agent-boolean>
    local controller_address="$1"
    local is_agent="$2"

    echo "[Info]: Upgrading controller: $controller_address..."
    [[ $is_agent = True ]] && echo "[Info]: Controller is also an agent."

    # create temp directory on controller node; capture dir name in CTEMP
    local CTEMP="$($SSH 2>/dev/null "$controller_address" "mktemp -d" | tr -d '[[:space:]]')"

    # copy over new vsm repo
    $SCP $REPO $controller_address:$CTEMP/vsmrepo

    # dump original vsm database to data save file
    MYSQL_ROOT_PASSWORD=`ssh $controller_address cat /etc/vsmdeploy/deployrc | grep ROOT | awk -F "=" '{print $2}'`

    $SSH $controller_address "bash -x -s" <<EOF
# dump old db data
$SUDO mysqldump -uroot -p$MYSQL_ROOT_PASSWORD -t vsm > $CTEMP/vsm.sql

# capture old db version
$SUDO vsm-manage db version > $CTEMP/vsm.old.version

# drop original vsm database
$SUDO mysql -uroot -p$MYSQL_ROOT_PASSWORD <<REMOTE_EOF
DROP DATABASE IF EXISTS vsm;
REMOTE_EOF

# save old controller configuration files
$SUDO cp -f /usr/share/vsm-dashboard/vsm_dashboard/local/local_settings.py $CTEMP
$SUDO cp -f /etc/vsmdeploy/deployrc $CTEMP
$SUDO cp -f /etc/vsm/ceph.conf.template $CTEMP
$SUDO cp -f /etc/vsm/rootwrap.conf $CTEMP
$SUDO cp -f /etc/vsm/vsm.conf $CTEMP
$SUDO cp -f /etc/manifest/cluster.manifest $CTEMP

# save old agent config files if controller is also an agent
if [[ $is_agent = True ]]; then
    $SUDO cp -f /etc/vsm/api-paste.ini $CTEMP
    $SUDO cp -f /etc/manifest/server.manifest $CTEMP
fi

# apt: purge original vsm packages (purge in case vsm files changed packages during upgrade)
$SUDO apt-get purge -y vsm vsm-deploy vsm-dashboard python-vsmclient

# remove original vsm repo
$SUDO rm -rf /opt/vsmrepo

# move vsm repo from $CTEMP over to /opt
$SUDO mv -f $CTEMP/vsmrepo /opt

# apt: clean, update, and install new vsm packages
$SUDO apt-get clean
$SUDO apt-get update
$SUDO apt-get install -y vsm vsm-deploy vsm-dashboard python-vsmclient

# restore saved original agent config files if controller is also an agent
if [[ "${is_agent}" = True ]]; then
    $SUDO mv -f $CTEMP/server.manifest /etc/manifest
fi

# restore saved original configuration files
$SUDO mv -f $CTEMP/cluster.manifest /etc/manifest
$SUDO mv -f $CTEMP/vsm.conf /etc/vsm
$SUDO mv -f $CTEMP/rootwrap.conf /etc/vsm
$SUDO mv -f $CTEMP/ceph.conf.template /etc/vsm
$SUDO mv -f $CTEMP/deployrc /etc/vsmdeploy

# create the new vsm database
$SUDO mysql -uroot -p$MYSQL_ROOT_PASSWORD <<REMOTE_EOF
CREATE DATABASE vsm;
REMOTE_EOF

# sync, save current db version, downgrade to old version
$SUDO vsm-manage db sync
$SUDO vsm-manage db version > $CTEMP/vsm.new.version
$SUDO vsm-manage db sync \$(cat $CTEMP/vsm.old.version)

# delete all rows from all vsm tables
for table in \$(echo 'SHOW TABLES' | mysql -uroot -p$MYSQL_ROOT_PASSWORD vsm | grep -v "Tables_in"); do\
  echo "DELETE FROM \$table;"; done | mysql -uroot -p$MYSQL_ROOT_PASSWORD vsm

# import old vsm data, upgrade to current version
$SUDO mysql -uroot -p$MYSQL_ROOT_PASSWORD -t vsm < $CTEMP/vsm.sql
$SUDO vsm-manage db sync \$(cat $CTEMP/vsm.new.version)

# restore original vsm-dashboard local_settings.py file
$SUDO mv -f $CTEMP/local_settings.py /usr/share/vsm-dashboard/vsm_dashboard/local

# start all controller services
$SUDO service apache2 restart
$SUDO service vsm-api restart
$SUDO service vsm-conductor restart
$SUDO service vsm-scheduler restart

# start all agent services if controller is also an agent
if [[ $is_agent = True ]]; then
    $SUDO service vsm-agent restart
    $SUDO service vsm-physical restart
fi
EOF
}

function upgrade_agent() {          # upgrade_agent <agent-address>
    local agent_address="$1"

    echo "[Info]: Upgrading agent: $agent_address..."

    # create temp directory on agent node; capture dir name in ATEMP
    local ATEMP="$($SSH 2>/dev/null "$agent_address" "mktemp -d" | tr -d '[[:space:]]')"

    # copy over new vsm repo
    $SCP $REPO $agent_address:$ATEMP/vsmrepo

    $SSH $agent_address "bash -x -s" <<EOF
# save off original vsm configuration files
$SUDO cp -f /etc/vsm/ceph.conf.template $ATEMP
$SUDO cp -f /etc/vsm/api-paste.ini $ATEMP
$SUDO cp -f /etc/vsm/vsm.conf $ATEMP
$SUDO cp -f /etc/manifest/server.manifest $ATEMP

# apt: purge original vsm packages (purge in case vsm files changed packages during upgrade)
$SUDO apt-get purge -y vsm vsm-deploy

# remove original vsm package repo
$SUDO rm -rf /opt/vsmrepo

# move vsm repo from $ATEMP over to /opt
$SUDO mv -f $ATEMP/vsmrepo /opt

# apt: clean, update, and install new vsm packages
$SUDO apt-get clean
$SUDO apt-get update
$SUDO apt-get install -y vsm vsm-deploy

# restore original vsm configuration files
$SUDO mv -f $ATEMP/ceph.conf.template /etc/vsm
$SUDO mv -f $ATEMP/api-paste.ini /etc/vsm
$SUDO mv -f $ATEMP/vsm.conf /etc/vsm
$SUDO mv -f $ATEMP/server.manifest /etc/manifest

# restart agent vsm services
$SUDO service vsm-agent restart
$SUDO service vsm-physical restart
EOF
}

function pre_upgrade() {            # pre_upgrade <controller-address> <agent-addr1>[,<agent-addr2>,...,<agent-addrN>]
    local controller_address="$1"
    local agent_address_list="${2//,/ }"

    for agent_address in $agent_address_list; do
        $SSH $agent_address "bash -x -s" <<EOF
# stop all agent vsm services
$SUDO service vsm-agent stop
$SUDO service vsm-physical stop
EOF
    done

    $SSH $controller_address "bash -x -s" <<EOF
# stop all controller vsm services
$SUDO service vsm-api stop
$SUDO service vsm-conductor stop
$SUDO service vsm-scheduler stop
EOF
}

# main

if [[ ! $CONTROLLER_ADDRESS ]]; then
    echo "[Error]: Please specify controller address."
    exit 1
fi

if [[ ! $AGENT_ADDRESS_LIST ]]; then
    echo "[Error]: Please specify agent address list."
    exit 1
fi

# run pre_upgrade to stop all vsm services on all nodes
set +e
( pre_upgrade $CONTROLLER_ADDRESS $AGENT_ADDRESS_LIST )
pre_upgrade_error="$?"
set -e
set +o xtrace
if [[ "${pre_upgrade_error}" -ne 0 ]]; then
    echo "[Error]: Pre-upgrade failed with error: $pre_upgrade_error."
    exit "${pre_upgrade_error}"
fi
set -o xtrace

# check to see if controller is also an agent and remove controller from agent list
CONTROLLER_IS_AGENT=False
if [[ "$AGENT_ADDRESS_LIST" == *"$CONTROLLER_ADDRESS"* ]]; then
    CONTROLLER_IS_AGENT=True
    AGENT_ADDRESS_LIST="${AGENT_ADDRESS_LIST/"${CONTROLLER_ADDRESS}"/}"
fi

# upgrade vsm on controller node
set +e
( upgrade_controller $CONTROLLER_ADDRESS $CONTROLLER_IS_AGENT )
upgrade_ctrl_error="$?"
set -e
set +o xtrace
if [[ "${upgrade_ctrl_error}" -ne 0 ]]; then
    echo "[Error]: Controller upgrade failed with error: $upgrade_ctrl_error."
    exit "${upgrade_ctrl_error}"
fi
set -o xtrace

# upgrade vsm on pure agent node
declare -A pids
declare -A tf_list
agent_address_list="${AGENT_ADDRESS_LIST//,/ }"
echo "[Info]: Starting asynchronous agent upgrade on [${agent_address_list}]."
for agent_address in $agent_address_list; do
    tf="$(mktemp)"
    tf_list[${agent_address}]="${tf}"
    ( upgrade_agent $agent_address >${tf} 2>&1 ) &
    pids[${agent_address}]="$!"
done

# wait for agents to complete upgrading in background
exit_code=0
declare -A errors
for agent_address in ${agent_address_list}; do
    set +e
    wait "${pids[${agent_address}]}"
    errors[${agent_address}]="$?"
    set -e
    if [[ "${errors[${agent_address}]}" -ne 0 ]]; then
        exit_code=1
    fi
done

# cat each agent log to the screen in startup order
# capture the log errors in case of failure
for agent_address in ${agent_address_list}; do
    cat "${tf_list[${agent_address}]}"
done

# print last 10 lines of each failing agent's log
set +o xtrace
if [[ "${exit_code}" -ne 0 ]]; then
    echo "[Error]: One or more agent upgrades failed."
    echo "[Error]: Displaying the last 10 lines of failed agent output:"
    for agent_address in ${agent_address_list}; do
        if [[ "${errors[${agent_address}]}" -ne 0 ]]; then
            echo "[Error]: Agent [${agent_address}] failed:"
            echo "..."
            tail -n 10 "${tf_list[${agent_address}]}"
        fi
    done
fi
set -o xtrace

# delete all temporary agent logs
for agent_address in ${agent_address_list}; do
    rm -f "${tf_list[${agent_address}]}"
done

if [[ "${exit_code}" -ne 0 ]]; then
    exit "${exit_code}"
else
    echo  "[Info]: Successfully upgraded VSM."
fi

set +o xtrace
