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
    The tool can help you to deploy the vsm envirement automatically.
    Please run such as bash +x install.sh

Options:
  --help | -h
    Print usage information.
  --manifest [manifest directory] | -m [manifest directory]
    The directory to store the server.manifest and cluster.manifest.
  --version [master] | -v [master]
    The version of vsm dependences to download(Default=master).
  --keyfile [key file] | -k [key file]
    The key file required for ssh/scp connection at the environment where certificate based authentication is enabled.
  --user | -u
    The user will be used to connect remote nodes to deploy vsm
EOF
    exit 0
}

MANIFEST_PATH=""
DEPENDENCE_BRANCH="2.1"
USER=`whoami`
SSH='ssh'
SCP='scp'
while [ $# -gt 0 ]; do
  case "$1" in
    -h) usage ;;
    --help) usage ;;
    -m| --manifest) shift; MANIFEST_PATH=$1 ;;
    -v| --version) shift; DEPENDENCE_BRANCH=$1 ;;
	-k| --key) shift; keyfile=$1; export SSH='ssh -i $keyfile'; export SCP='scp -i $keyfile' ;;
    -u| --user) shift; USER=$1 ;;
    *) shift ;;
  esac
  shift
done


set -e
set -o xtrace

echo "Before auto deploy the vsm, please be sure that you have set the manifest 
such as manifest/192.168.100.100/server.manifest. And you have changed the file, too."
sleep 5

TOPDIR=$(cd $(dirname "$0") && pwd)
TEMP=`mktemp`; rm -rfv $TEMP >/dev/null; mkdir -p $TEMP;

HOSTNAME=`hostname`
#HOSTIP=`hostname -I|sed s/[[:space:]]//g`
HOSTIP=`hostname -I`

source $TOPDIR/installrc

is_controller=0
for ip in $HOSTIP; do
    if [ $ip == $CONTROLLER_ADDRESS ]; then
        is_controller=1
    fi
done

if [[ $HOSTNAME == $CONTROLLER_ADDRESS ]]; then
    is_controller=1
fi

if [ $is_controller -eq 0 ]; then
    echo "[Info]: You run the tool in a third server."
else
    echo "[Info]: You run the tool in the controller server."
fi


#-------------------------------------------------------------------------------
#            checking packages
#-------------------------------------------------------------------------------

echo "+++++++++++++++start checking packages+++++++++++++++"

if [ ! -d vsmrepo ]; then
    echo "You should have the vsmrepo folder, please check and try again"
    exit 1
fi

cd vsmrepo
is_python_vsmclient=`ls|grep -E "python-vsmclient*.+((deb)$|(rpm)$)"|wc -l`
is_vsm=`ls|grep -v python-vsmclient|grep -v vsm-dashboard|grep -v vsm-deploy|grep vsm|wc -l`
is_vsm_dashboard=`ls|grep -E "vsm-dashboard*.+((deb)$|(rpm)$)"|wc -l`
is_vsm_deploy=`ls|grep -E "vsm-deploy*.+((deb)$|(rpm)$)"|wc -l`
if [ $is_python_vsmclient -gt 0 ] && [ $is_vsm -gt 0 ] && [ $is_vsm_dashboard -gt 0 ] && [ $is_vsm_deploy -gt 0 ]; then
    echo "The vsm pachages have been already prepared"
else
    echo "please check the vsm packages, then try again"
    exit 1
fi

cd $TOPDIR
echo "+++++++++++++++finish checking packages+++++++++++++++"

function check_distro() {
	distro_check=`cat /proc/version | grep -i $1 | wc -l`
}
check_distro ubuntu

# install the requirement packages for ubuntu
if [ $distro_check -eq 1 ]; then
sudo apt-get install unzip
fi

#-------------------------------------------------------------------------------
#            setting the iptables and selinux
#-------------------------------------------------------------------------------

echo "+++++++++++++++start setting the iptables and selinux+++++++++++++++"

function set_iptables_selinux() {
    $SSH $USER@$1 "service iptables stop"
    $SSH $USER@$1 "chkconfig iptables off"
    $SSH $USER@$1 "sed -i \"s/SELINUX=enforcing/SELINUX=disabled/g\" /etc/selinux/config"
#    $SSH $USER@$1 "setenforce 0"
}

# these things are only valid when we are ina selinux environment
if [ $distro_check -eq 0 ]; then

	if [ $is_controller -eq 0 ]; then
	    set_iptables_selinux $CONTROLLER_ADDRESS
	else
	    service iptables stop
	    chkconfig iptables off
	    sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config
	#    setenforce 0
	fi


	for ip in $AGENT_ADDRESS_LIST; do
	    set_iptables_selinux $ip
	done

	echo "+++++++++++++++finish setting the iptables and selinux+++++++++++++++"
fi


#-------------------------------------------------------------------------------
#            downloading the dependences
#-------------------------------------------------------------------------------

if [ $distro_check -eq 0 ]; then

	if [ ! -d /opt/vsm-dep-repo ] && [ ! -d vsm-dep-repo ]; then
	    if [ ! -f "$DEPENDENCE_BRANCH".zip ]; then
	    	wget https://github.com/01org/vsm-dependencies/archive/"$DEPENDENCE_BRANCH".zip
	    fi
	    unzip $DEPENDENCE_BRANCH
	    mv vsm-dependencies-$DEPENDENCE_BRANCH/repo vsm-dep-repo
	    is_createrepo=`rpm -qa|grep createrepo|wc -l`
	    if [[ $is_createrepo -gt 0 ]]; then
		createrepo vsm-dep-repo
	    fi
	    rm -rf vsm-dependencies-$DEPENDENCE_BRANCH
	    rm -rf $DEPENDENCE_BRANCH
	fi
else
	if [ ! -d /opt/vsm-dep-repo ] && [ ! -d vsm-dep-repo ]; then
	    if [ ! -f "$DEPENDENCE_BRANCH".zip ]; then
		# this downloads both deb and rpm files
	    	wget https://github.com/01org/vsm-dependencies/archive/"$DEPENDENCE_BRANCH".zip
	    fi
	    unzip "$DEPENDENCE_BRANCH".zip
	    mv vsm-dependencies-$DEPENDENCE_BRANCH/ubuntu14 vsm-dep-repo
	    #lets copy the vsm file to this repo also so that we can install them via apt-get
	    #dpkg does not have localinstall
            sudo cp vsmrepo/*.deb vsm-dep-repo
            #ends
	    is_createrepo=`which dpkg-scanpackages|wc -l`
	    if [[ $is_createrepo -gt 0 ]]; then
		cd vsm-dep-repo
 	        dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz
		cd -
	    fi
	    rm -rf vsm-dependencies-$DEPENDENCE_BRANCH
	    rm -rf $DEPENDENCE_BRANCH
	fi
	
fi

if [ $is_controller -eq 0 ]; then
    $SSH $USER@$CONTROLLER_ADDRESS "sudo rm -rf /opt/vsm-dep-repo"
    $SCP -r vsm-dep-repo $USER@$CONTROLLER_ADDRESS:~
    $SSH $USER@$CONTROLLER_ADDRESS "sudo mv ~/vsm-dep-repo /opt"

else
    if [ -d vsm-dep-repo ]; then
        sudo rm -rf /opt/vsm-dep-repo
        sudo cp -rf vsm-dep-repo /opt
    else
        sudo cp -rf vsm-dep-repo /opt
    fi
fi


#-------------------------------------------------------------------------------
#            setting the repo
#-------------------------------------------------------------------------------

echo "+++++++++++++++start setting the repo+++++++++++++++"


if [ $distro_check -eq 0 ]; then

	is_httpd=`rpm -qa|grep httpd|grep -v httpd-tools|wc -l`
	if [[ $is_httpd -gt 0 ]]; then
	    sudo sed -i "s,#*Listen 80,Listen 80,g" /etc/httpd/conf/httpd.conf
	    sudo service httpd restart
	fi
else
	is_httpd=`dpkg -l|grep -E '\sapache2\s'|wc -l`
	if [[ $is_httpd -gt 0 ]]; then
	    sudo sed -i "s,#*Listen 80,Listen 80,g" /etc/apache2/ports.conf
	    sudo service apache2 restart
	else
	    sudo apt-get install -y apache2
	    sudo apt-get --reinstall install -y libapache2-mod-wsgi
	fi

fi


if [ $distro_check -eq 0 ]; then

rm -rf vsm.repo
        cat << 'EOF' > vsm.repo
	[vsm-dep-repo]
	name=vsm-dep-repo
	baseurl=file:///opt/vsm-dep-repo
	gpgcheck=0
	enabled=1
	proxy=_none_
EOF


else
	rm -rf vsm.list
	cat <<EOF > vsm.list
	deb file:/opt/vsm-dep-repo ./
EOF
fi

if [ $distro_check -eq 0 ]; then

	oldurl="file:///opt/vsm-dep-repo"
	newurl="http://$CONTROLLER_ADDRESS/vsm-dep-repo"
	if [ $is_controller -eq 0 ]; then
	    $SCP vsm.repo $USER@$CONTROLLER_ADDRESS:/etc/yum.repos.d
	    $SSH $USER@$CONTROLLER_ADDRESS "yum makecache; yum -y install httpd; service httpd restart; rm -rf /var/www/html/vsm-dep-repo; cp -rf /opt/vsm-dep-repo /var/www/html"
	    $SSH $USER@$CONTROLLER_ADDRESS "sed -i \"s,$oldurl,$newurl,g\" /etc/yum.repos.d/vsm.repo; yum makecache"
	else
	    cp vsm.repo /etc/yum.repos.d
	    yum makecache; yum -y install httpd; service httpd restart; rm -rf /var/www/html/vsm-dep-repo; cp -rf /opt/vsm-dep-repo /var/www/html
	    sed -i "s,$oldurl,$newurl,g" /etc/yum.repos.d/vsm.repo
	    yum makecache
	fi
else
	oldurl="file:/opt/vsm-dep-repo"
	newurl="http://$CONTROLLER_ADDRESS/vsm-dep-repo"
	if [ $is_controller -eq 0 ]; then
            $SCP vsm.list $USER@$CONTROLLER_ADDRESS:~
	    $SSH $USER@$CONTROLLER_ADDRESS "sudo mv ~/vsm.list /etc/apt/sources.list.d"
            $SSH $USER@$CONTROLLER_ADDRESS "sudo apt-get update; sudo apt-get -y install apache2 libapache2-mod-wsgi; sudo service apache2 restart; sudo rm -rf /var/www/html/vsm-dep-repo; sudo cp -rf /opt/vsm-dep-repo /var/www/html"
            $SSH $USER@$CONTROLLER_ADDRESS "sudo sed -i \"s,$oldurl,$newurl,g\" /etc/apt/sources.list.d/vsm.list; sudo apt-get update"
	else
	    sudo cp vsm.list /etc/apt/sources.list.d
            sudo apt-get update; sudo apt-get -y install apache2 libapache2-mod-wsgi; sudo service apache2 restart; sudo rm -rf /var/www/html/vsm-dep-repo; sudo cp -rf /opt/vsm-dep-repo /var/www/html
            sudo sed -i "s,$oldurl,$newurl,g" /etc/apt/sources.list.d/vsm.list
            sudo apt-get update
	fi

fi

sed -i "s,$oldurl,$newurl,g" vsm.list

function set_repo() {
    if [ $distro_check -eq 0 ]; then
	    $SSH $USER@$1 "rm -rf /etc/yum.repos.d/vsm.repo"
	    $SCP vsm.repo $USER@$1:/etc/yum.repos.d
	    $SSH $USER@$1 "yum makecache"
    else

	   # se the ceph repo so that the dependencies like python-rb and others will be installed from the repo
	    $SSH $USER@$1 "sudo apt-get purge -y ceph ceph-mds librbd1 rbd-fuse; sudo apt-get autoremove -y"
	    $SSH $USER@$1 "wget -q -O- 'https://download.ceph.com/keys/release.asc' | sudo apt-key add -"
	    $SSH $USER@$1 "sudo apt-add-repository 'deb http://download.ceph.com/debian-hammer/ trusty main'"
	
	    $SSH $USER@$1 "sudo rm -rf /etc/apt/sources.list.d/vsm.list"
            $SCP vsm.list $USER@$1:~
	    $SSH  $USER@$1 "sudo mv ~/vsm.list /etc/apt/sources.list.d"
            $SSH $USER@$1 "sudo apt-get update"
    fi
}

for ip in $AGENT_ADDRESS_LIST; do
    set_repo $ip
done

echo "+++++++++++++++finish setting the repo+++++++++++++++"


#-------------------------------------------------------------------------------
#            install vsm rpm and dependences
#-------------------------------------------------------------------------------

echo "+++++++++++++++install vsm rpm and dependences+++++++++++++++"

function install_vsm_controller() {
    if [ $distro_check -eq 0 ]; then
	    $SSH $USER@$1 "mkdir -p /opt/vsm_install"
	    $SCP vsmrepo/python-vsmclient*.rpm vsmrepo/vsm*.rpm $USER@$1:/opt/vsm_install
	    $SSH $USER@$1 "cd /opt/vsm_install; yum -y localinstall python-vsmclient*.rpm vsm*.rpm"
	    $SSH $USER@$1 "sudo preinstall"
	    $SSH $USER@$1 "cd /opt; rm -rf /opt/vsm_install"
    else
	    $SSH $USER@$1 "sudo sudo mkdir -p /opt/vsm_install"
	    $SCP vsmrepo/python-vsmclient*.deb vsmrepo/vsm*.deb $USER@$1:~
            $SSH $USER@$1 "sudo mv ~/vsmrepo/python-vsmclient*.deb ~/vsmrepo/vsm*.deb /opt/vsm_install"
	    #$SSH $USER@$1 "cd /opt/vsm_install; sudo dpkg -i python-vsmclient*.deb vsm*.deb"
	    $SSH $USER@$1 "cd /opt/vsm_install; sudo apt-get install -y --force-yes python-vsmclient vsm vsm-dashboard vsm-deploy"
	    #patch required to fix the unsigned package installation
	    $SSH $USER@$1 "wget https://github.com/oguzy/virtual-storage-manager/raw/master/preinstall.patch -O /tmp/preinstall.patch"
	    $SSH $USER@$1 "sudo patch /usr/local/bin/preinstall < /tmp/preinstall.patch"
	    $SSH $USER@$1 "rm /tmp/preinstall.patch"
	    $SSH $USER@$1 "sudo preinstall"
	    $SSH $USER@$1 "cd /opt; sudo rm -rf /opt/vsm_install"
	    
    fi
}

function install_vsm_storage() {
    if [ $distro_check -eq 0 ]; then
	    $SSH $USER@$1 "mkdir -p /opt/vsm_install"
	    $SCP vsmrepo/vsm*.rpm $USER@$1:/opt/vsm_install
	    $SSH $USER@$1 "cd /opt/vsm_install; rm -rf vsm-dashboard*; yum -y localinstall vsm*.rpm"
	    $SSH $USER@$1 "sudo preinstall"
	    $SSH $USER@$1 "cd /opt; rm -rf /opt/vsm_install"
    else
	    $SSH $USER@$1 "sudo mkdir -p /opt/vsm_install"
	    #$SCP vsmrepo/vsm*.deb $USER@$1:/opt/vsm_install
	    $SCP vsmrepo/vsm*.deb $USER@$1:~
	    $SSH $USER@$1 "sudo mv ~/vsm*.deb /opt/vsm_install"
	    #$SSH $USER@$1 "cd /opt/vsm_install; sudo rm -rf vsm-dashboard*; sudo dpkg -i vsm*.deb"
	    $SSH $USER@$1 "cd /opt/vsm_install; sudo rm -rf vsm-dashboard; sudo apt-get -y --force-yes install vsm vsm-deploy"
	    #patch required to fix the unsigned package installation
	    $SSH $USER@$1 "wget https://github.com/oguzy/virtual-storage-manager/raw/master/preinstall.patch -O /tmp/preinstall.patch"
	    $SSH $USER@$1 "sudo patch /usr/local/bin/preinstall < /tmp/preinstall.patch"
	    $SSH $USER@$1 "rm /tmp/preinstall.patch"
	    $SSH $USER@$1 "sudo preinstall agent"
	    $SSH $USER@$1 "cd /opt; sudo rm -rf /opt/vsm_install"
    fi
}

if [ $distro_check -eq 0 ]; then

	if [ $is_controller -eq 0 ]; then
	    install_vsm_controller $CONTROLLER_ADDRESS
	else
	    yum -y localinstall vsmrepo/python-vsmclient*.rpm vsmrepo/vsm*.rpm
	    preinstall
	fi

else
	if [ $is_controller -eq 0 ]; then
	    install_vsm_controller $CONTROLLER_ADDRESS
	else
	    #sudo dpkg -i  vsmrepo/python-vsmclient*.deb vsmrepo/vsm*.deb
	    sudo apt-get -y --force-yes install python-vsmclient vsm vsm-dashboard vsm-deploy
	    #patch required to fix the unsigned package installation
	    wget https://github.com/oguzy/virtual-storage-manager/raw/master/preinstall.patch -O /tmp/preinstall.patch
	    sudo patch /usr/local/bin/preinstall < /tmp/preinstall.patch
	    rm /tmp/preinstall.patch
	    sudo preinstall
	fi
fi

for ip in $AGENT_ADDRESS_LIST; do
    install_vsm_storage $ip
done

echo "+++++++++++++++finish install vsm rpm and dependences+++++++++++++++"


#-------------------------------------------------------------------------------
#            setup vsm controller node
#-------------------------------------------------------------------------------

if [ -z $MANIFEST_PATH ]; then
    MANIFEST_PATH="manifest"
fi

function setup_controller() {
    $SSH $USER@$CONTROLLER_ADDRESS "sudo rm -rf /etc/manifest/cluster_manifest"
    #$SCP $MANIFEST_PATH/$CONTROLLER_ADDRESS/cluster.manifest $USER@$CONTROLLER_ADDRESS:/etc/manifest
    $SCP $MANIFEST_PATH/$CONTROLLER_ADDRESS/cluster.manifest $USER@$CONTROLLER_ADDRESS:~
    $SSH $USER@$CONTROLLER_ADDRESS "sudo mv ~/cluser.manifest /etc/manifest"
    $SSH $USER@$CONTROLLER_ADDRESS "sudo chown root:vsm /etc/manifest/cluster.manifest; sudo chmod 755 /etc/manifest/cluster.manifest"
    is_cluster_manifest_error=`$SSH $USER@$CONTROLLER_ADDRESS "sudo cluster_manifest|grep error|wc -l"`
    if [ $is_cluster_manifest_error -gt 0 ]; then
        echo "please check the cluster.manifest, then try again"
        exit 1
    else
	# since there is no getip command, better to use the eth2 address
	# whihc is not so neath solution though
	$SSH $USER@$CONTROLLER_ADDRESS "sudo patch /usr/local/bin/vsm-controller < vsm-controller.patch"
        $SSH $USER@$CONTROLLER_ADDRESS "sudo vsm-controller"
    fi
}

if [ $is_controller -eq 0 ]; then
    setup_controller
else
    sudo rm -rf /etc/manifest/cluster.manifest
    sudo cp $MANIFEST_PATH/$CONTROLLER_ADDRESS/cluster.manifest /etc/manifest
    sudo chown root:vsm /etc/manifest/cluster.manifest
    sudo chmod 755 /etc/manifest/cluster.manifest
    if [ `sudo cluster_manifest|grep error|wc -l` -gt 0 ]; then
        echo "please check the cluster.manifest, then try again"
        exit 1
    else
	sudo patch /usr/local/bin/vsm-controller < vsm-controller.patch
        sudo patch /usr/local/bin/keys/https < https.patch
        sudo vsm-controller
    fi
fi


#-------------------------------------------------------------------------------
#            setup vsm storage node
#-------------------------------------------------------------------------------

count_ip=0
for ip in $AGENT_ADDRESS_LIST; do
    let count_ip=$count_ip+1
done
let count_ip=$count_ip+2+1
if [ `ls $MANIFEST_PATH|wc -l` != $count_ip ]; then
    echo "please check the manifest folder"
    exit 1
fi

success=""
failure=""
if [ $is_controller -eq 0 ]; then
    token=`$SSH $USER@$CONTROLLER_ADDRESS "sudo agent-token"`
else
    token=`sudo agent-token`
fi

function setup_storage() {
    $SSH $USER@$1 "sudo rm -rf /etc/manifest/server.manifest"
    #sed -i "s/token-tenant/$token/g" $MANIFEST_PATH/$1/server.manifest
    #old_str=`cat $MANIFEST_PATH/$1/server.manifest| grep ".*-.*" | grep -v by | grep -v "\["`
    #sed -i "s/$old_str/$token/g" $MANIFEST_PATH/$1/server.manifest
    sudo sed -i "/^\[auth_key\]$/,/^\[.*\]/ s/^.*-.*$/$TOKEN/" $MANIFEST_PATH/$1/server.manifest
    #$SCP $MANIFEST_PATH/$1/server.manifest $USER@$1:/etc/manifest
    $SCP $MANIFEST_PATH/$1/server.manifest $USER@$1:~
    $SSH $USER@$1 "sudo mv ~/server.manifest /etc/manifest"
    $SSH $USER@$1 "sudo chown root:vsm /etc/manifest/server.manifest; sudo chmod 755 /etc/manifest/server.manifest"
    is_server_manifest_error=`$SSH $USER@$1 "sudo server_manifest" |grep ERROR|wc -l`
    if [ $is_server_manifest_error -gt 0 ]; then
        echo "[warning]: The server.manifest in $1 is wrong, so fail to setup in $1 storage node"
        failure=$failure"$1 "
    else
        $SSH $USER@$1 "sudo vsm-node"
        success=$success"$1 "
    fi
}

for ip in $AGENT_ADDRESS_LIST; do
    setup_storage $ip
done


#-------------------------------------------------------------------------------
#            finish auto deploy
#-------------------------------------------------------------------------------

echo "Successful storage node ip: $success"
echo "Failure storage node ip: $failure"

set +o xtrace
