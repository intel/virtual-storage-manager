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
while getopts "h?kmadc" opt; do
    case "$opt" in
    h|\?)
        echo "Uninstall VSM and other components and clean up any remaining file system items and processes."
        echo "By default: Uninstall VSM, RabbitMQ, Diamond, and Ceph components."
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
    esac
done

set -o xtrace

TOPDIR=$(cd $(dirname "$0") && pwd)
USER=`whoami`

source $TOPDIR/installrc

VSM_DEP_PKGS="alembic apache2 apache2-bin apache2-data binutils build-essential ceph ceph-common\
 ceph-fs-common ceph-fuse ceph-mds cpp cpp-4.8 cryptsetup-bin diamond dpkg-dev erlang-asn1 erlang-base\
 erlang-corba erlang-crypto erlang-diameter erlang-edoc erlang-eldap erlang-erl-docgen erlang-eunit\
 erlang-ic erlang-inets erlang-mnesia erlang-nox erlang-odbc erlang-os-mon erlang-parsetools erlang-percept\
 erlang-public-key erlang-runtime-tools erlang-snmp erlang-ssh erlang-ssl erlang-syntax-tools erlang-tools\
 erlang-webtool erlang-xmerl expect fakeroot fontconfig fontconfig-config fonts-dejavu-core fonts-liberation\
 g++ g++-4.8 gcc gcc-4.8 gdisk graphviz heirloom-mailx ieee-data keystone libaio1:amd64 libalgorithm-diff-perl\
 libalgorithm-diff-xs-perl libalgorithm-merge-perl libapache2-mod-wsgi libapr1:amd64 libaprutil1:amd64\
 libaprutil1-dbd-sqlite3:amd64 libaprutil1-ldap:amd64 libasan0:amd64 libatomic1:amd64 libblas3\
 libboost-system1.54.0:amd64 libboost-thread1.54.0:amd64 libc6-dev:amd64 libcairo2:amd64 libc-dev-bin\
 libcdt5 libcephfs1 libcgraph6 libcloog-isl4:amd64 libcryptsetup4 libdatrie1:amd64 libdbd-mysql-perl\
 libdbi-perl libdpkg-perl libfakeroot:amd64 libfile-fcntllock-perl libfontconfig1:amd64 libgcc-4.8-dev:amd64\
 libgd3:amd64 libgfortran3:amd64 libgmp10:amd64 libgomp1:amd64 libgoogle-perftools4 libgraphite2-3:amd64\
 libgvc6 libgvpr2 libharfbuzz0b:amd64 libhtml-template-perl libice6:amd64 libicu52:amd64 libisl10:amd64\
 libitm1:amd64 libjbig0:amd64 libjpeg8:amd64 libjpeg-turbo8:amd64 libjs-jquery libjs-sphinxdoc\
 libjs-underscore liblapack3 libleveldb1:amd64 libltdl7:amd64 libmariadbclient18:amd64 libmpc3:amd64\
 libmpfr4:amd64 libmysqlclient18:amd64 libnspr4:amd64 libnss3:amd64 libnss3-nssdb libodbc1:amd64\
 libopts25:amd64 libpango-1.0-0:amd64 libpangocairo-1.0-0:amd64 libpangoft2-1.0-0:amd64 libpathplan4\
 libpixman-1-0:amd64 libquadmath0:amd64 librabbitmq1 librados2 librbd1 libsctp1:amd64 libsm6:amd64\
 libsnappy1 libstdc++-4.8-dev:amd64 libtcl8.6:amd64 libtcmalloc-minimal4 libterm-readkey-perl libthai0:amd64\
 libthai-data libtiff5:amd64 libtsan0:amd64 libunwind8 libvpx1:amd64 libxaw7:amd64 libxcb-render0:amd64\
 libxcb-shm0:amd64 libxmu6:amd64 libxpm4:amd64 libxrender1:amd64 libxslt1.1:amd64 libxt6:amd64\
 libyaml-0-2:amd64 linux-libc-dev:amd64 lksctp-tools make manpages-dev mariadb-client-5.5\
 mariadb-client-core-5.5 mariadb-common mariadb-server mariadb-server-5.5 mariadb-server-core-5.5\
 memcached mysql-common ntp python-alembic python-amqp python-amqplib python-anyjson python-appconf\
 python-babel python-babel-localedata python-backports.ssl-match-hostname python-blinker\
 python-ceilometerclient python-ceph python-cinderclient python-cliff python-cliff-doc python-cmd2\
 python-compressor python-concurrent.futures python-crypto python-dbus python-dbus-dev python-decorator\
 python-django python-django-horizon python-django-pyscss python-dns python-dogpile.cache python-dogpile.core\
 python-ecdsa python-eventlet python-flask python-formencode python-gi python-glanceclient python-greenlet\
 python-heatclient python-httplib2 python-iso8601 python-itsdangerous python-jinja2 python-jsonpatch\
 python-json-patch python-json-pointer python-jsonschema python-keyring python-keystone python-keystoneclient\
 python-keystonemiddleware python-kombu python-ldap python-ldappool python-librabbitmq python-lockfile\
 python-lxml python-mako python-markupsafe python-memcache python-migrate python-mock python-mysqldb\
 python-netaddr python-neutronclient python-novaclient python-numpy python-oauthlib python-openid\
 python-openstack-auth python-oslo.config python-oslo.db python-oslo.i18n python-oslo.messaging\
 python-oslo.serialization python-oslo.utils python-paramiko python-passlib python-paste python-pastedeploy\
 python-pastedeploy-tpl python-pastescript python-pbr python-posix-ipc python-prettytable python-psutil\
 python-pycadf python-pyinotify python-pyparsing python-pyscss python-repoze.lru python-routes\
 python-saharaclient python-scgi python-secretstorage python-setuptools python-simplejson python-sqlalchemy\
 python-sqlalchemy-ext python-stevedore python-suds python-support python-swiftclient python-tempita\
 python-troveclient python-tz python-versiontools python-vsmclient python-warlock python-webob python-werkzeug\
 python-yaml rabbitmq-server rbd-fuse smartmontools ssl-cert vsm vsm-dashboard vsm-deploy x11-common xfsprogs"

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
sudo apt-get autoremove --yes
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
sudo apt-get autoremove --yes
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

