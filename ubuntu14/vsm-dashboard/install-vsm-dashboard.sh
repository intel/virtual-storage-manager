#!/bin/bash
#
# Small script to install vsm-dashboard to local filesystem

export VSM_DASHBOARD_ROOT_PATH=debian/vsm-dashboard

rm -rf build

#---------------------------
# httpd Configuration file
#---------------------------
install -g root -o root -v -m 755 -d $VSM_DASHBOARD_ROOT_PATH/etc/apache2/conf-available
install -g root -o root -v -m 755 -t $VSM_DASHBOARD_ROOT_PATH/etc/apache2/conf-available tools/vsm-dashboard.conf

#---------------------------
# bin Files for lessc
#---------------------------
install -g root -o root -v -m 755 -d $VSM_DASHBOARD_ROOT_PATH/usr/bin
install -g root -o root -v -m 755 -t $VSM_DASHBOARD_ROOT_PATH/usr/bin bin/less/lessc
install -g root -o root -v -m 755 -d $VSM_DASHBOARD_ROOT_PATH/usr/lib
cp -av bin/lib/less $VSM_DASHBOARD_ROOT_PATH/usr/lib

#---------------------------
# Source files.
#---------------------------
install -g root -o root -v -m 755 -d $VSM_DASHBOARD_ROOT_PATH/usr/share/vsm-dashboard
cp -av vsm_dashboard $VSM_DASHBOARD_ROOT_PATH/usr/share/vsm-dashboard
cp -av static $VSM_DASHBOARD_ROOT_PATH/usr/share/vsm-dashboard
install -g root -o root -v -m 755 -t $VSM_DASHBOARD_ROOT_PATH/usr/share/vsm-dashboard manage.py