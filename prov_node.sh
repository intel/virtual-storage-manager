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


TOPDIR=$(cd $(dirname "$0") && pwd)
USER=`whoami`
VERSION=`cat VERSION`

usage() {
	echo "Usage: $0 <manifest file> <ip address> <host name>"
	exit -1
}

if [ $@ -lt 3 ]; then
	usage
fi

manifest=$1
ip=$2
host=$3

server_manifest $manifest

if [ $? ]; then
	echo "some errors found in server manifest file, please correct them first"
	exit -2
fi

ssh-copy-id $ip

sudo echo "$ip	$host" >>/etc/hosts

mkdir -p ${TOPDIR}/manifest/$ip
cp $manifest ${TOPDIR}/manifest/$ip/server.manifest

${TOPDIR}/install.sh --agent $ip -v ${VERSION%.*}


