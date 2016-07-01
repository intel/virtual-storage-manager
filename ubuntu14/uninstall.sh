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
AUTO_REMOVE_DEPS=1

# Parse command line options to change defaults
OPTIND=1
while getopts "h?kmadcr" opt; do
    case "$opt" in
    h|\?)
        echo "Uninstall VSM and other components and clean up any remaining file system items and processes."
        echo "By default: Uninstall VSM, RabbitMQ, Diamond, and Ceph components."
        echo "By default: Autoremove secondary package dependencies."
        echo "By default: Do NOT uninstall MySQL/MariaDB components."
        echo "By default: Do NOT uninstall Apache2 server components."
        echo "By default: Do NOT uninstall Keystone components."
        echo "By default: Do NOT uninstall all VSM dependency packages on controller."
        echo ""
        echo "Usage: uninstall.sh [options]"
        echo "options:"
        echo "   -k  Uninstall Keystone components."
        echo "   -m  Uninstall MySQL/MariaDB components."
        echo "   -a  Uninstall Apache2 server components."
        echo "   -d  Uninstall all VSM dependency packages on controller."
        echo "   -c  Suppress removal of Ceph cluster and components."
        echo "   -r  Suppress auto-remove of secondary dependencies."
        exit 0
        ;;
    k)  REMOVE_KEYSTONE_PKGS=1
        ;;
    m)  REMOVE_MYSQL_PKGS=1
        ;;
    a)  REMOVE_APACHE2_PKGS=1
        ;;
    d)  REMOVE_VSM_DEP_PKGS=1
        ;;
    c)  unset REMOVE_CEPH_PKGS
        ;;
    r)  unset AUTO_REMOVE_DEPS
        ;;
    esac
done

set -o xtrace

TOPDIR=$(cd $(dirname "$0") && pwd)
USER=`whoami`

source $TOPDIR/installrc

# build a list of package names from a directory specified in an apt .list file
function deps_from_local_repo()
{
    for deb in "$1"/*.deb; do
        PKG_NAME="$(dpkg-deb -f ${deb} Package 2>/dev/null)"
        if test ! -z "${PKG_NAME}" && grep "${PKG_NAME}" "$2" >/dev/null 2>&1; then
            echo -n "${PKG_NAME} "
        fi
    done
}

VSM_DEP_PKGS="$(deps_from_local_repo vsm-dep-repo debs.lst)"

function uninstall_controller()
{
    echo "=== Uninstall controller [$1] start."
    ssh -t $1 'bash -x -s' <<EOF
if [ -n "${REMOVE_CEPH_PKGS}" ]; then
    sudo clean-data -f
fi
sudo service vsm-api stop
sudo service vsm-scheduler stop
sudo service vsm-conductor stop
test -d /etc/mysql && sudo service mysql restart
test -d /etc/rabbitmq && sudo service rabbitmq-server restart
sleep 3
sudo apt-get purge --yes vsm vsm-dashboard python-vsmclient vsm-deploy
sudo apt-get purge --yes rabbitmq-server librabbitmq1
sudo killall rabbitmq-server beam beam.smp
sudo apt-get purge --yes diamond
if [ -n "${REMOVE_KEYSTONE_PKGS}" ]; then
    sudo apt-get purge --yes keystone python-keystone python-keystoneclient python-keystonemiddleware
    sudo rm -rf /var/lib/keystone /etc/keystone
fi
if [ -n "${REMOVE_MYSQL_PKGS}" ]; then
    sudo apt-get purge --yes mariadb-client-5.5 mariadb-client-core-5.5
    sudo apt-get purge --yes mariadb-server mariadb-server-5.5 mariadb-server-core-5.5
    sudo apt-get purge --yes libdbd-mysql-perl libmysqlclient18:amd64 mysql-common python-mysqldb
    sudo killall mysqld
    sudo rm -rf /etc/mysql /var/lib/mysql
fi
if [ -n "${REMOVE_APACHE2_PKGS}" ]; then
    sudo apt-get purge --yes apache2 apache2-bin apache2-data libapache2-mod-wsgi
    sudo killall apache2
    sudo rm -rf /etc/apache2
fi
if [ -n "${REMOVE_VSM_DEP_PKGS}" ]; then
    sudo apt-get purge --yes ${VSM_DEP_PKGS}
fi
if [ -n "${AUTO_REMOVE_DEPS}" ]; then
    sudo apt-get autoremove --yes
fi
sudo apt-get autoclean --yes
sudo rm -rf /etc/vsm /etc/vsm-dashboard /etc/vsmdeploy /var/lib/vsm /var/log/vsm
sudo rm -rf /opt/vsmrepo /opt/vsm-dep-repo
sudo rm -f /etc/apt/sources.list.d/vsm.list /etc/apt/sources.list.d/vsm-dep.list
EOF
    echo "=== Uninstall controller [$1] complete."
}

function uninstall_agent()
{
echo "=== Uninstall agent [$1] start."
    ssh -t $1 'bash -x -s' <<EOF
if [ -n "${REMOVE_CEPH_PKGS}" ]; then
    sudo clean-data -f
fi
sudo service vsm-agent stop
sudo service vsm-physical stop
sudo apt-get purge --yes vsm vsm-dashboard python-vsmclient vsm-deploy
sudo apt-get purge --yes diamond
sudo apt-get purge --yes python-keystoneclient
if [ -n "${REMOVE_MYSQL_PKGS}" ]; then
    sudo apt-get purge --yes libdbd-mysql-perl libmysqlclient18:amd64 mysql-common python-mysqldb
    sudo rm -rf /etc/mysql
fi
if [ -n "${AUTO_REMOVE_DEPS}" ]; then
    sudo apt-get autoremove --yes
fi
sudo apt-get autoclean --yes
sudo rm -rf /var/lib/vsm /var/log/vsm /etc/vsm
sudo rm -rf /opt/vsmrepo /opt/vsm-dep-repo
sudo rm -f /etc/apt/sources.list.d/vsm.list /etc/apt/sources.list.d/vsm-dep.list
EOF
    echo "=== Uninstall agent [$1] complete."
}

# remove controller in the foreground
uninstall_controller $CONTROLLER_ADDRESS

# remove all agents simultaneously; wait for all to finish
for ip in $AGENT_ADDRESS_LIST; do
    tf=$(mktemp)
    tf_list="${tf_list} ${tf}"
    echo "=== Starting asynchronous agent uninstall [$ip] ..."
    uninstall_agent $ip >${tf} 2>&1 &
done
wait
for tf in ${tf_list}; do cat ${tf}; rm -f ${tf}; done

