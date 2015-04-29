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

VERSION="1.1"
while [ $# -gt 0 ]; do
  case "$1" in
    -h) usage ;;
    --help) usage ;;
    -v| --version) VERSION=$2 ;;
    *) shift ;;
  esac
  shift
done

set -e
set -o xtrace

TOPDIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null; mkdir -p $TEMP;
DATE=`date "+%Y%m%d"`

is_lsb_release=0
lsb_release -a >/dev/null 2>&1 && is_lsb_release=1

if [[ $is_lsb_release -gt ]]; then
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
mkdir -p $TEMP_VSM/release/$VERSION-$DATE
cp -rf * $TEMP_VSM
cp -rf .lib $TEMP_VSM
cd $TEMP_VSM

function create_release() {
    if [[ $OS == "Ubuntu" && $OS_VERSION == "14.04" ]]; then
        cp ubuntu14/builddeb .
        bash +x builddeb
        sudo cp ubuntu14/install.sh release/$VERSION-$DATE
    elif [[ $OS == "CentOS" && $OS_VERSION == "7" ]]; then
        pass
    elif [[ $OS == "CentOS" && $OS_VERSION == "6.5" ]]; then
        pass
    fi

    sudo cp README.md release/$VERSION-$DATE/README
    sudo cp INSTALL.md release/$VERSION-$DATE
    sudo cp LICENSE release/$VERSION-$DATE
    sudo cp NOTICE release/$VERSION-$DATE
    sudo cp CHANGELOG release/$VERSION-$DATE
    sudo cp hostrc release/$VERSION-$DATE
    sudo cp -r manifest release/$VERSION-$DATE
    sudo cp -r vsmrepo release/$VERSION-$DATE

    cd release
    tar -czvf $VERSION-$DATE.tar.gz $VERSION-$DATE
    rm -rf $VERSION-$DATE
    cp -r $TEMP_VSM/release $TOPDIR

}

create_release

rm -rf $TEMP_VSM

set +o xtrace
