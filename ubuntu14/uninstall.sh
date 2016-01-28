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

# Defaults
REMOVE_CEPH_PKGS=1

# Parse command line options to change defaults
OPTIND=1
while getopts "h?kc" opt; do
    case "$opt" in
    h|\?)
        echo "Uninstall VSM and other components and clean up any remaining file system items and processes."
        echo "By default: Uninstall VSM, RabbitMQ, Diamond, and Ceph components."
        echo "By default: Do NOT uninstall Keystone components.
        echo ""
        echo "Usage: uninstall.sh [options]"
        echo "options:"
        echo "   -k  Uninstall Keystone components."
        echo "   -c  Suppress removal of Ceph cluster and components."
        exit 0
        ;;
    k)  REMOVE_KEYSTONE_PKGS=1
        ;;
    c)  unset REMOVE_CEPH_PKGS
        ;;
    esac
done

set -o xtrace

TOPDIR=$(cd $(dirname "$0") && pwd)
USER=`whoami`

source $TOPDIR/installrc

for ip in $CONTROLLER_ADDRESS; do
    ssh -t $ip 'bash -x -s' <<EOF
if [ -n "${REMOVE_CEPH_PKGS}" ]; then
    sudo clean-data -f
fi
sudo service vsm-api stop
sudo service vsm-scheduler stop
sudo service vsm-conductor stop
sudo service mysql restart
sudo service rabbitmq-server restart
sleep 3
sudo apt-get purge --yes vsm vsm-dashboard python-vsmclient vsm-deploy
sudo apt-get purge --yes rabbitmq-server librabbitmq1
sudo killall rabbitmq-server beam.smp
sudo apt-get purge --yes diamond
if [ -n "${REMOVE_KEYSTONE_PKGS}" ]; then
    sudo apt-get purge --yes keystone python-keystone python-keystoneclient python-keystonemiddleware
    sudo rm -rf /var/lib/keystone /etc/keystone
fi
sudo apt-get autoremove --yes
sudo apt-get autoclean --yes
sudo rm -rf /etc/vsm /etc/vsm-dashboard /etc/vsmdeploy /var/lib/vsm /var/log/vsm
EOF
done

for ip in $AGENT_ADDRESS_LIST; do
    ssh -t $ip 'bash -x -s' <<EOF
if [ -n "${REMOVE_CEPH_PKGS}" ]; then
    sudo clean-data -f
fi
sudo service vsm-agent stop
sudo service vsm-physical stop
sudo apt-get purge --yes vsm vsm-dashboard python-vsmclient vsm-deploy
sudo apt-get purge --yes diamond
sudo apt-get purge --yes python-keystoneclient
sudo apt-get autoremove --yes
sudo apt-get autoclean --yes
sudo rm -rf /var/lib/vsm /var/log/vsm /etc/vsm
EOF
done

