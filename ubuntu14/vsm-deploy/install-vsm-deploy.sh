#!/bin/bash
#
# Small script to install vsm-deploy to local filesystem

export VSM_DEPLOY_ROOT_PATH=debian/vsm-deploy

getent group vsm >/dev/null || sudo groupadd -r vsm --gid 165
if ! getent passwd vsm >/dev/null; then
  sudo useradd -u 165 -r -g vsm -G vsm,nogroup -d /var/lib/vsm -s /usr/sbin/nologin -c "Vsm Storage Services" vsm
fi

#---------------------------
# etc/manifest/
#---------------------------
install -g root -o root -d -m 755 $VSM_DEPLOY_ROOT_PATH/etc/manifest/
install -g root -o vsm -v -p -D -m 755 tools/etc/vsm/cluster.manifest $VSM_DEPLOY_ROOT_PATH/etc/manifest/
install -g root -o vsm -v -p -D -m 755 tools/etc/vsm/server.manifest $VSM_DEPLOY_ROOT_PATH/etc/manifest/

#---------------------------
# usr/local/bin/
#---------------------------
install -g root -o root -d -m 755 $VSM_DEPLOY_ROOT_PATH/usr/local/bin/
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ __clean-data
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ cache-tier-defaults
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ clean-data
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ downloadrepo
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ ec-profile
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ preinstall
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ replace-str
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ reset_status
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ restart-all
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ rpm.lst
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ rpms_list
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ start_osd
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ sync-code
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ vsm-checker
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ vsm-controller
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ vsm-installer
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ vsm-node
install -g root -o vsm -v -m 755 -t $VSM_DEPLOY_ROOT_PATH/usr/local/bin/ vsm-update

cp -rf keys $VSM_DEPLOY_ROOT_PATH/usr/local/bin/
cp -rf tools $VSM_DEPLOY_ROOT_PATH/usr/local/bin/
chown -R vsm:root $VSM_DEPLOY_ROOT_PATH/usr/local/bin/keys
chown -R vsm:root $VSM_DEPLOY_ROOT_PATH/usr/local/bin/tools
