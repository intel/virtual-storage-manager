%global with_doc %{!?_without_doc:1}%{?_without_doc:0}
%define version %{getenv:VERSION}
%define release %{getenv:RELEASE}

Name:             vsm
Version:          %{version}
Release:          %{release}
Summary:          Virtual Storage Manager for managing Ceph clusters

Group:            Storage/System
License:          Intel
URL:              http://intel.com
Source:           %{name}-%{version}.tar.gz

BuildArch:        noarch
BuildRequires:    MySQL-python
BuildRequires:    python-ordereddict
BuildRequires:    python-pbr
BuildRequires:    python-decorator
BuildRequires:    python-tempita
BuildRequires:    python-sqlalchemy
BuildRequires:    python-amqplib
BuildRequires:    python-anyjson
BuildRequires:    python-eventlet
BuildRequires:    python-kombu
BuildRequires:    python-lockfile
BuildRequires:    python-lxml
BuildRequires:    python-routes
BuildRequires:    python-webob
BuildRequires:    python-greenlet
BuildRequires:    python-paste-deploy
BuildRequires:    python-paste
BuildRequires:    python-migrate
BuildRequires:    python-stevedore
BuildRequires:    python-suds
BuildRequires:    python-paramiko
BuildRequires:    python-babel
BuildRequires:    python-iso8601
BuildRequires:    python-keystoneclient
BuildRequires:    python-oslo-config
BuildRequires:    numpy
BuildRequires:    python-psutil

Requires:    MySQL-python
Requires:    python-ordereddict
Requires:    python-pbr
Requires:    python-decorator
Requires:    python-tempita
Requires:    python-sqlalchemy
Requires:    python-amqplib
Requires:    python-anyjson
Requires:    python-eventlet
Requires:    python-kombu
Requires:    python-lockfile
Requires:    python-lxml
Requires:    python-routes
Requires:    python-webob
Requires:    python-greenlet
Requires:    python-paste-deploy
Requires:    python-paste
Requires:    python-migrate
Requires:    python-stevedore
Requires:    python-suds
Requires:    python-paramiko
Requires:    python-babel
Requires:    python-iso8601
Requires:    python-keystoneclient
Requires:    python-oslo-config
Requires:    numpy
Requires:    ceph
Requires:    btrfs-progs
Requires:    xfsprogs
Requires:    python-psutil
Requires:    mod_ssl

%description
Virtual Storage Manager (VSM) is software that Intel has developed to help manage Ceph clusters. VSM simplifies the creation and day-to-day management of Ceph cluster for cloud and datacenter storage administrators.

%if 0%{?with_doc}
%package doc
Summary:          Documentation for Virtual Storage Manager for Ceph
Group:            Documentation

#Requires:         %{name} = %{version}-%{release}
BuildRequires:    graphviz
BuildRequires:    python-eventlet
BuildRequires:    python-routes
BuildRequires:    python-sqlalchemy
BuildRequires:    python-webob
BuildRequires:    python-migrate
BuildRequires:    python-iso8601

%description      doc
OpenStack Volume (codename Cinder) provides services to manage and
access block storage volumes for use by Virtual Machine instances.

This package contains documentation files for vsm.
%endif

%prep
%setup -q -n %{name}-%{version}
sed -i '/setup_requires/d; /install_requires/d; /dependency_links/d' setup.py

%build

mkdir -p %{buildroot}
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

#---------------------------
# Log files
#---------------------------
install -d -m 755 %{buildroot}%{_sharedstatedir}/vsm
install -d -m 755 %{buildroot}%{_sharedstatedir}/vsm/tmp
install -d -m 755 %{buildroot}%{_localstatedir}/log/vsm

#---------------------------
# Config files
#---------------------------

install -d -m 755 %{buildroot}%{_sysconfdir}/vsm/rootwrap.d
install -d -m 755 %{buildroot}%{_sysconfdir}/vsm
install -d -m 755 %{buildroot}%{_sysconfdir}/sudoers.d
install -p -D -m 640 etc/vsm/vsm.conf.sample %{buildroot}%{_sysconfdir}/vsm/vsm.conf
install -p -D -m 640 etc/vsm/ceph.conf.template %{buildroot}%{_sysconfdir}/vsm/ceph.conf.template
install -p -D -m 640 etc/vsm/rootwrap.conf %{buildroot}%{_sysconfdir}/vsm/rootwrap.conf
install -p -D -m 640 etc/vsm/cache-tier.conf %{buildroot}%{_sysconfdir}/vsm/cache-tier.conf
install -p -D -m 640 etc/vsm/api-paste.ini %{buildroot}%{_sysconfdir}/vsm/api-paste.ini
install -p -D -m 640 etc/vsm/policy.json %{buildroot}%{_sysconfdir}/vsm/policy.json
install -p -D -m 640 etc/vsm/logging_sample.conf %{buildroot}%{_sysconfdir}/vsm/logging.conf
install -p -D -m 640 etc/vsm/rootwrap.d/vsm.filters %{buildroot}%{_sysconfdir}/vsm/rootwrap.d/vsm.filters
install -p -D -m 440 etc/sudoers.d/vsm %{buildroot}%{_sysconfdir}/sudoers.d/vsm
install -p -D -m 640 etc/logrotate.d/vsmceph %{buildroot}%{_sysconfdir}/logrotate.d/vsmceph

#---------------------------
#  SSH Keys
#---------------------------
# TODO check this line whether is needed
#cp -rf etc/vsm/*.sh %{buildroot}%{_sysconfdir}/vsm/


#---------------------------
#  Prepools
#---------------------------

install -d -m 755 %{buildroot}%{_sysconfdir}/vsm/
cp -rf etc/vsm/prepools %{buildroot}%{_sysconfdir}/vsm/


#---------------------------
# etc/init.d/
#---------------------------
install -d -m 755 %{buildroot}%{_initrddir}
install -p -D -m 755 etc/init.d/vsm-physical %{buildroot}%{_initrddir}/vsm-physical
install -p -D -m 755 etc/init.d/vsm-agent %{buildroot}%{_initrddir}/vsm-agent
install -p -D -m 755 etc/init.d/vsm-api %{buildroot}%{_initrddir}/vsm-api
install -p -D -m 755 etc/init.d/vsm-conductor %{buildroot}%{_initrddir}/vsm-conductor
install -p -D -m 755 etc/init.d/vsm-scheduler %{buildroot}%{_initrddir}/vsm-scheduler


#---------------------------
# usr/bin/
#---------------------------

install -d -m 755 %{buildroot}%{_bindir}/
install -p -D -m 755 bin/vsm-api %{buildroot}%{_bindir}/vsm-api
install -p -D -m 755 bin/vsm-agent %{buildroot}%{_bindir}/vsm-agent
install -p -D -m 755 bin/vsm-physical %{buildroot}%{_bindir}/vsm-physical
install -p -D -m 755 bin/vsm-conductor %{buildroot}%{_bindir}/vsm-conductor
install -p -D -m 755 bin/vsm-scheduler %{buildroot}%{_bindir}/vsm-scheduler
install -p -D -m 755 bin/vsm-rootwrap %{buildroot}%{_bindir}/vsm-rootwrap
install -p -D -m 755 bin/key %{buildroot}%{_bindir}/key
install -p -D -m 755 bin/auto_key_gen %{buildroot}%{_bindir}/auto_key_gen
install -p -D -m 755 bin/vsm-assist %{buildroot}%{_bindir}/vsm-assist
install -p -D -m 755 bin/presentpool %{buildroot}%{_bindir}/presentpool
install -p -D -m 755 bin/rbd_ls %{buildroot}%{_bindir}/rbd_ls
install -p -D -m 755 bin/agent-token %{buildroot}%{_bindir}/agent-token
install -p -D -m 755 bin/admin-token %{buildroot}%{_bindir}/admin-token
install -p -D -m 755 bin/vsm-backup %{buildroot}%{_bindir}/vsm-backup
install -p -D -m 755 bin/vsm-restore %{buildroot}%{_bindir}/vsm-restore
install -p -D -m 755 bin/cluster_manifest %{buildroot}%{_usr}/local/bin/cluster_manifest
install -p -D -m 755 bin/server_manifest  %{buildroot}%{_usr}/local/bin/server_manifest
install -p -D -m 755 bin/refresh-osd-status %{buildroot}%{_usr}/local/bin/refresh-osd-status
install -p -D -m 755 bin/refresh-cluster-status %{buildroot}%{_usr}/local/bin/refresh-cluster-status
install -p -D -m 755 bin/getip  %{buildroot}%{_usr}/local/bin/getip
install -p -D -m 755 bin/import_ceph_conf  %{buildroot}%{_usr}/local/bin/import_ceph_conf
install -p -D -m 755 bin/get_smart_info %{buildroot}%{_bindir}/get_smart_info
install -p -D -m 755 bin/kill_diamond %{buildroot}%{_bindir}/kill_diamond
install -p -D -m 755 bin/vsm-ceph-upgrade %{buildroot}%{_bindir}/vsm-ceph-upgrade

install -p -D -m 755 tools/get_storage %{buildroot}%{_usr}/local/bin/get_storage
install -p -D -m 755 tools/spot_info_list %{buildroot}%{_usr}/local/bin/spot_info_list
install -p -D -m 755 tools/vsm-reporter.py %{buildroot}%{_usr}/local/bin/vsm-reporter
install -p -D -m 755 bin/intergrate-cluster %{buildroot}%{_usr}/local/bin/intergrate-cluster

%pre
getent group vsm >/dev/null || groupadd -r vsm --gid 165
if ! getent passwd vsm >/dev/null; then
  useradd -u 165 -r -g vsm -G vsm,nobody -d %{_sharedstatedir}/vsm -s /sbin/nologin -c "Vsm Storage Services" vsm
fi
mkdir -p /var/run/vsm/
mkdir -p /var/log/vsm/
mkdir -p /var/lib/vsm
mkdir -p /etc/vsm/
mkdir -p /etc/vsm/rootwrap.d
chown -R vsm /var/run/vsm
chown -R vsm /var/log/vsm/
chown -R vsm /var/lib/vsm
chown -R vsm /etc/vsm/
if [ -f /etc/init.d/ceph ]; then
    sed -i 's,do_cmd.* 30 $BINDIR.*,do_cmd "timeout 30 $BINDIR/ceph -c $conf --name=osd.$id --keyring=$osd_keyring osd crush create-or-move -- $id ${osd_weight:-${defaultweight:-1}} $osd_location ||:",g' /etc/init.d/ceph;
    sed -i 's,do_cmd.* 30 $BINDIR.*,do_cmd "timeout 30 $BINDIR/ceph -c $conf --name=osd.$id --keyring=$osd_keyring osd crush create-or-move -- $id ${osd_weight:-${defaultweight:-1}} $osd_location ||:",g' /etc/init.d/ceph;

fi

exit 0


%files
%defattr(-,root,root,-)
%doc LICENSE doc
%{python_sitelib}/*

%dir %{_sysconfdir}/logrotate.d
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/logrotate.d/vsmceph
%dir %attr(-, vsm, vsm) /var/log/vsm
%dir %attr(-, vsm, vsm) /var/lib/vsm
%dir %{_sysconfdir}/vsm
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/vsm.conf
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/ceph.conf.template
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/api-paste.ini
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/rootwrap.conf
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/policy.json
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/logging.conf
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/cache-tier.conf
%dir %{_sysconfdir}/vsm/rootwrap.d
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/rootwrap.d/vsm.filters

#%dir %{_sysconfdir}/sudoers.d
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/sudoers.d/vsm

%dir %{_initrddir}
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-physical
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-agent
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-api
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-conductor
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-scheduler

#%dir %{_bindir}
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-rootwrap
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-physical
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-agent
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-api
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-conductor
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-all
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-manage
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-scheduler
%config(noreplace) %attr(-, root, vsm) %{_bindir}/key
%config(noreplace) %attr(-, root, vsm) %{_bindir}/auto_key_gen
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-assist
%config(noreplace) %attr(-, root, vsm) %{_bindir}/presentpool
%config(noreplace) %attr(-, root, vsm) %{_bindir}/rbd_ls
%config(noreplace) %attr(-, root, vsm) %{_bindir}/agent-token
%config(noreplace) %attr(-, root, vsm) %{_bindir}/admin-token
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-backup
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-restore
%config(noreplace) %attr(-, root, vsm) %{_bindir}/get_smart_info
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/intergrate-cluster
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/import_ceph_conf
%config(noreplace) %attr(-, root, vsm) %{_bindir}/kill_diamond
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-ceph-upgrade

%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/getip
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/cluster_manifest
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/server_manifest
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/refresh-osd-status
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/refresh-cluster-status

%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/get_storage
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/spot_info_list
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/vsm-reporter


#-----------------------------
# Prepools
#-----------------------------
%dir %{_sysconfdir}/vsm/prepools
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/prepools/*
# TODO check this line whether needed
