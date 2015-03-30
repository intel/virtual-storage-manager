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
Usage: packvsm

Pack vsm:
    The tool can help you to pack all into a folder to setup vsm.
    Please run such as bash +x packvsm

Options:
  --help | -h
    Print usage information.
  --name | -n
    The folder name.
EOF
    exit 0
}

FOLDER_NAME="vsm-package"
while [ $# -gt 0 ]; do
  case "$1" in
    -h) usage ;;
    --help) usage ;;
    -n| --name) FOLDER_NAME=$2 ;;
    *) shift ;;
  esac
  shift
done

set -e
set -o xtrace

TOPDIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null; mkdir -p $TEMP;

mkdir -p release/$FOLDER_NAME

bash +x buildrpm

cp README.md release/$FOLDER_NAME/README
cp INSTALL.md release/$FOLDER_NAME
cp install.sh release/$FOLDER_NAME
cp LICENSE release/$FOLDER_NAME
cp NOTICE release/$FOLDER_NAME
cp CHANGELOG release/$FOLDER_NAME
cp hostrc release/$FOLDER_NAME
cp -r manifest release/$FOLDER_NAME
cp -r vsmrepo release/$FOLDER_NAME

cd release
tar -czvf $FOLDER_NAME.tar.gz $FOLDER_NAME
rm -rf $FOLDER_NAME
cd $TOPDIR

set +o xtrace
