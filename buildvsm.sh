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
Usage: $0

Pack vsm:
    The tool can help to pull all necessary documents, binaries into one place,
    and maintain an expected folder structure for following release package generation.

Options:
  --help | -h
    Print usage information.
  --version | -v
    The version of release vsm.
EOF
    exit 0
}

VERSION=`cat VERSION`
BUILD=`cat BUILD`
RELEASE=${VERSION}_${BUILD}
echo $((++BUILD)) > BUILD

while [ $# -gt 0 ]; do
  case "$1" in
    -h) usage ;;
    --help) usage ;;
    -v| --version) shift; VERSION=$1 ;;
    *) shift ;;
  esac
  shift
done

set -e
set -o xtrace

TOPDIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null; mkdir -p $TEMP;
#DATE=`date "+%Y%m%d"`

is_lsb_release=0
lsb_release -a >/dev/null 2>&1 && is_lsb_release=1

if [[ $is_lsb_release -gt 0 ]]; then
    OS=`lsb_release -a|grep "Distributor ID:"|awk -F ' ' '{print $3}'`
    OS_VERSION=`lsb_release -a|grep "Release"|awk -F ' ' '{print $2}'`
else
    var=`cat /etc/os-release|grep "PRETTY_NAME"|awk -F "=" '{print $2}'`
    if [[ $var =~ "CentOS Linux 7" ]]; then
        OS="CentOS"
        OS_VERSION="7"
    fi
fi

TEMP_VSM=`mktemp`; rm -rfv $TEMP_VSM >/dev/null; mkdir -p $TEMP_VSM;
mkdir -p $TEMP_VSM/release/$RELEASE
cp -rf * $TEMP_VSM
cp -rf .lib $TEMP_VSM
if [ -d ubuntu14/.lib ]; then
    cp -rf ubuntu14/.lib $TEMP_VSM/ubuntu14/.lib
fi
cd $TEMP_VSM

function create_release() {
    if [[ $OS == "Ubuntu" && $OS_VERSION =~ "14" ]]; then
        cp -rf ubuntu14/.lib .
        cp -rf ubuntu14/python-vsmclient ./source
        cp -rf ubuntu14/vsm ./source
        cp -rf ubuntu14/vsm-dashboard ./source
        cp -rf ubuntu14/vsm-deploy ./source
        cp ubuntu14/builddeb .
        bash +x builddeb
        cp ubuntu14/install.sh release/$RELEASE
        cp ubuntu14/debs.lst release/$RELEASE
    elif [[ $OS == "CentOS" && $OS_VERSION == "7" ]]; then
        cp -rf centos7/python-vsmclient ./source
        cp -rf centos7/vsm ./source
        cp -rf centos7/vsm-dashboard ./source
        cp -rf centos7/vsm-deploy ./source
        cp centos7/buildrpm .
        bash +x buildrpm
        cp centos7/install.sh release/$RELEASE
    elif [[ $OS =~ "SUSE" ]]; then
        cp -rf suse/python-vsmclient ./source
        cp -rf suse/vsm ./source
        cp -rf suse/vsm-dashboard ./source
        cp -rf suse/vsm-deploy ./source
        cp suse/buildrpm .
        bash +x buildrpm
    elif [[ $OS == "CentOS" && $OS_VERSION =~ "6" ]]; then
        bash +x buildrpm
        cp install.sh release/$RELEASE
    fi

    cp README.md release/$RELEASE/README
    cp INSTALL.md release/$RELEASE
    cp LICENSE release/$RELEASE
    cp NOTICE release/$RELEASE
    cp CHANGELOG.md release/$RELEASE
    cp hostrc release/$RELEASE
#    cp -r manifest release/$RELEASE
    mkdir -p release/$RELEASE/manifest
    cp source/vsm/etc/vsm/cluster.manifest release/$RELEASE/manifest/cluster.manifest.sample
    cp source/vsm/etc/vsm/server.manifest release/$RELEASE/manifest/server.manifest.sample
    cp -r vsmrepo release/$RELEASE

    cd release
    tar -czvf $RELEASE.tar.gz $RELEASE
    rm -rf $RELEASE
    cp -r $TEMP_VSM/release $TOPDIR
    cp -r $TEMP_VSM/vsmrepo $TOPDIR

}

create_release

rm -rf $TEMP_VSM

set +o xtrace

