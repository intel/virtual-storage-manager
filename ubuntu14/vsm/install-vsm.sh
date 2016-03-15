#!/bin/bash
#
# Small script to install vsm to local filesystem

export VSM_ROOT_PATH=debian/vsm

getent group vsm >/dev/null || groupadd -r vsm --gid 165
if ! getent passwd vsm >/dev/null; then
  useradd -u 165 -r -g vsm -G vsm,nogroup -d /var/lib/vsm -s /usr/sbin/nologin -c "Vsm Storage Services" vsm
fi

python setup.py install -O1 --skip-build --root $VSM_ROOT_PATH

#---------------------------
# Log files
#---------------------------


#---------------------------
# Config files
#---------------------------
install -g root -o root -v -m 755 -d $VSM_ROOT_PATH/etc/vsm
install -g root -o root -v -m 755 -d $VSM_ROOT_PATH/etc/vsm/rootwrap.d
install -g root -o root -v -m 755 -d $VSM_ROOT_PATH/etc/sudoers.d
install -g root -o root -v -m 755 -d $VSM_ROOT_PATH/etc/logrotate.d
install -g root -o vsm -v -m 640 -t $VSM_ROOT_PATH/etc/vsm etc/vsm/vsm.conf.sample
install -g root -o vsm -v -m 640 -t $VSM_ROOT_PATH/etc/vsm etc/vsm/ceph.conf.template
install -g root -o vsm -v -m 640 -t $VSM_ROOT_PATH/etc/vsm etc/vsm/rootwrap.conf
install -g root -o vsm -v -m 640 -t $VSM_ROOT_PATH/etc/vsm etc/vsm/cache-tier.conf
install -g root -o vsm -v -m 640 -t $VSM_ROOT_PATH/etc/vsm etc/vsm/api-paste.ini
install -g root -o vsm -v -m 640 -t $VSM_ROOT_PATH/etc/vsm etc/vsm/policy.json
install -g root -o vsm -v -m 640 -t $VSM_ROOT_PATH/etc/vsm etc/vsm/logging_sample.conf
install -g root -o vsm -v -m 640 -t $VSM_ROOT_PATH/etc/vsm/rootwrap.d etc/vsm/rootwrap.d/vsm.filters
install -g root -o root -v -m 640 -t $VSM_ROOT_PATH/etc/sudoers.d etc/sudoers.d/vsm
install -g root -o vsm -v -m 640 -t $VSM_ROOT_PATH/etc/logrotate.d etc/logrotate.d/vsmceph

#---------------------------
#  Prepools
#---------------------------
cp -av etc/vsm/prepools $VSM_ROOT_PATH/etc/vsm
chown vsm:root $VSM_ROOT_PATH/etc/vsm/prepools/*

#---------------------------
# etc/init.d/
#---------------------------
install -g root -o root -v -m 755 -d $VSM_ROOT_PATH/etc/init.d
install -g root -o root -v -m 755 -t $VSM_ROOT_PATH/etc/init.d etc/init.d/vsm-agent
install -g root -o root -v -m 755 -t $VSM_ROOT_PATH/etc/init.d etc/init.d/vsm-api
install -g root -o root -v -m 755 -t $VSM_ROOT_PATH/etc/init.d etc/init.d/vsm-conductor
install -g root -o root -v -m 755 -t $VSM_ROOT_PATH/etc/init.d etc/init.d/vsm-physical
install -g root -o root -v -m 755 -t $VSM_ROOT_PATH/etc/init.d etc/init.d/vsm-scheduler

#---------------------------
# usr/bin/
#---------------------------
install -g root -o root -v -m 755 -d $VSM_ROOT_PATH/usr/bin
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-api
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-agent
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-physical
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-conductor
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-all
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-manage
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-scheduler
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-rootwrap
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/key
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/auto_key_gen
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-assist
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/presentpool
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/rbd_ls
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/agent-token
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/admin-token
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-backup
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-restore
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/vsm-ceph-upgrade
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/exp_ceph_upgrade
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/exp_ceph-common_upgrade
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/bin bin/exp_ceph-mds_upgrade


#---------------------------
# usr/local/bin/
#---------------------------
install -g root -o root -v -m 755 -d $VSM_ROOT_PATH/usr/local/bin
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin bin/cluster_manifest
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin bin/server_manifest
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin bin/refresh-osd-status
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin bin/refresh-cluster-status
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin bin/check_xtrust_crudini
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin bin/getip
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin tools/get_storage
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin tools/spot_info_list
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin tools/vsm-reporter.py

install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin bin/import_ceph_conf
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin bin/get_smart_info
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin bin/kill_diamond
#install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/local/bin bin/vsm-ceph-upgrade
install -g root -o vsm -v -m 755 -t $VSM_ROOT_PATH/usr/sbin bin/nvme

mv $VSM_ROOT_PATH/usr/local/bin/vsm-reporter.py $VSM_ROOT_PATH/usr/local/bin/vsm-reporter
rm -rf $VSM_ROOT_PATH/usr/local/bin/vsm-agent
rm -rf $VSM_ROOT_PATH/usr/local/bin/vsm-all
rm -rf $VSM_ROOT_PATH/usr/local/bin/vsm-api
rm -rf $VSM_ROOT_PATH/usr/local/bin/vsm-conductor
rm -rf $VSM_ROOT_PATH/usr/local/bin/vsm-manage
rm -rf $VSM_ROOT_PATH/usr/local/bin/vsm-physical
rm -rf $VSM_ROOT_PATH/usr/local/bin/vsm-rootwrap
rm -rf $VSM_ROOT_PATH/usr/local/bin/vsm-scheduler

#---------------------------
# usr/share/doc
#---------------------------
install -g root -o root -v -m 640 -d $VSM_ROOT_PATH/usr/share/doc/vsm-2015.03
install -g root -o root -v -m 640 -t $VSM_ROOT_PATH/usr/share/doc/vsm-2015.03 LICENSE
cp -rf doc $VSM_ROOT_PATH/usr/share/doc/vsm-2015.03

# fix the file not included in the deb package
cp vsm/db/sqlalchemy/migrate_repo/migrate.cfg $VSM_ROOT_PATH/usr/local/lib/python2.7/dist-packages/vsm/db/sqlalchemy/migrate_repo

# fix the folder locale not included in the deb package
cp -rf vsm/locale $VSM_ROOT_PATH/usr/local/lib/python2.7/dist-packages/vsm

# fix the file not included in the deb package
cp vsm/diamond/diamond.conf $VSM_ROOT_PATH/usr/local/lib/python2.7/dist-packages/vsm/diamond
