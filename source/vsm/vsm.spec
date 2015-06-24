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
%if 0%{?suse_version}
BuildRequires:    python-MySQL-python
BuildRequires:    python-SQLAlchemy
BuildRequires:    python-sqlalchemy-migrate
BuildRequires:    python-Routes
BuildRequires:    python-PasteDeploy
BuildRequires:    fdupes
BuildRequires:    systemd-rpm-macros
BuildRequires:    aaa_base
# SLE 12
%if 0%{?suse_version} == 1315
BuildRequires:    python-cyordereddict
%else
BuildRequires:    python-ordereddict
%endif
%else
BuildRequires:    MySQL-python
BuildRequires:    python-sqlalchemy0.7
BuildRequires:    python-routes1.12
BuildRequires:    python-paste-deploy1.5
BuildRequires:    python-migrate
BuildRequires:    python-amqplib
BuildRequires:    python-importlib
BuildRequires:    python-ordereddict
%endif

BuildRequires:    python-pbr
BuildRequires:    python-decorator
BuildRequires:    python-tempita
BuildRequires:    python-anyjson
BuildRequires:    python-argparse
BuildRequires:    python-eventlet
BuildRequires:    python-kombu
BuildRequires:    python-lockfile
BuildRequires:    python-lxml
BuildRequires:    python-webob
BuildRequires:    python-greenlet
BuildRequires:    python-paste
BuildRequires:    python-stevedore
BuildRequires:    python-suds
BuildRequires:    python-paramiko
BuildRequires:    python-babel
BuildRequires:    python-iso8601
BuildRequires:    python-keystoneclient
BuildRequires:    python-oslo-config
BuildRequires:    numpy
BuildRequires:    python-psutil

%if 0%{?suse_version}
Requires:    python-MySQL-python
Requires:    python-SQLAlchemy
Requires:    python-sqlalchemy-migrate
Requires:    python-Routes
Requires:    python-PasteDeploy
Requires:    btrfsprogs
Requires:    logrotate
# SLE 12
%if 0%{?suse_version} == 1315
Requires:    python-cyordereddict
%else
Requires:    python-ordereddict
%endif
%{?systemd_requires}
%else
Requires:    MySQL-python
Requires:    python-sqlalchemy0.7
Requires:    python-routes1.12
Requires:    python-paste-deploy1.5
Requires:    python-migrate
Requires:    btrfs-progs
Requires:    mod_ssl
Requires:    python-amqplib
Requires:    python-importlib
Requires:    python-ordereddict
%endif

Requires:    python-pbr
Requires:    python-decorator
Requires:    python-tempita
Requires:    python-anyjson
Requires:    python-argparse
Requires:    python-eventlet
Requires:    python-kombu
Requires:    python-lockfile
Requires:    python-lxml
Requires:    python-webob
Requires:    python-greenlet
Requires:    python-paste
Requires:    python-stevedore
Requires:    python-suds
Requires:    python-paramiko
Requires:    python-babel
Requires:    python-iso8601
Requires:    python-keystoneclient
Requires:    python-oslo-config
Requires:    numpy
Requires:    ceph
Requires:    xfsprogs
Requires:    python-psutil

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
BuildRequires:    python-webob
BuildRequires:    python-iso8601

%if 0%{?suse_version}
BuildRequires:    python-SQLAlchemy
BuildRequires:    python-sqlalchemy-migrate
%else
BuildRequires:    python-sqlalchemy0.7
BuildRequires:    python-migrate
%endif

%description      doc
OpenStack Volume (codename Cinder) provides services to manage and
access block storage volumes for use by Virtual Machine instances.

This package contains documentation files for vsm.
%endif

%prep
%setup -q -n %{name}-%{version}
sed -i '/setup_requires/d; /install_requires/d; /dependency_links/d' setup.py

%build

%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

%if 0%{?suse_version}
install -d -m 755 %{buildroot}/var/log/vsm/
install -d -m 700 %{buildroot}/var/lib/vsm
install -d -m 755 %{buildroot}/etc/vsm/
install -d -m 755 %{buildroot}/etc/vsm/rootwrap.d
%else
mkdir -p %{buildroot}/var/log/vsm/
mkdir -p %{buildroot}/var/lib/vsm
mkdir -p %{buildroot}/etc/vsm/
mkdir -p %{buildroot}/etc/vsm/rootwrap.d
%endif

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
install -p -D -m 640 etc/sudoers.d/vsm %{buildroot}%{_sysconfdir}/sudoers.d/vsm

%if 0%{?suse_version}
install -p -D -m 640 etc/logrotate.d/vsm %{buildroot}%{_sysconfdir}/logrotate.d/vsm
%else
install -p -D -m 640 etc/logrotate.d/vsmceph %{buildroot}%{_sysconfdir}/logrotate.d/vsmceph
%endif

#---------------------------
#  SSH Keys
#---------------------------
# TODO check this line whether is needed
#cp -rf etc/vsm/*.sh %%{buildroot}%%{_sysconfdir}/vsm/


#---------------------------
#  Prepools
#---------------------------

install -d -m 755 %{buildroot}%{_sysconfdir}/vsm/
cp -rf etc/vsm/prepools %{buildroot}%{_sysconfdir}/vsm/


%if 0%{?suse_version}
#---------------------------
# usr/lib/systemd/system
#---------------------------
install -d -m 755 %{buildroot}%{_unitdir}
install -p -D -m 644 usr/lib/systemd/system/vsm-physical.service %{buildroot}%{_unitdir}/vsm-physical.service
install -p -D -m 644 usr/lib/systemd/system/vsm-agent.service %{buildroot}%{_unitdir}/vsm-agent.service
install -p -D -m 644 usr/lib/systemd/system/vsm-api.service %{buildroot}%{_unitdir}/vsm-api.service
install -p -D -m 644 usr/lib/systemd/system/vsm-conductor.service %{buildroot}%{_unitdir}/vsm-conductor.service
install -p -D -m 644 usr/lib/systemd/system/vsm-scheduler.service %{buildroot}%{_unitdir}/vsm-scheduler.service


install -d -m 755 %{buildroot}%{_sbindir}
ln -sf %_sbindir/service %{buildroot}%_sbindir/rcvsm-physical
ln -sf %_sbindir/service %{buildroot}%_sbindir/rcvsm-agent
ln -sf %_sbindir/service %{buildroot}%_sbindir/rcvsm-api
ln -sf %_sbindir/service %{buildroot}%_sbindir/rcvsm-conductor
ln -sf %_sbindir/service %{buildroot}%_sbindir/rcvsm-scheduler

install -d -m 755 %{buildroot}%{_tmpfilesdir}
install -m 0644 -D etc/systemd/vsm.tmpfiles.d %{buildroot}/%{_tmpfilesdir}/%{name}.conf
%else
#---------------------------
# etc/init.d/
#---------------------------
install -d -m 755 %{buildroot}%{_initrddir}
install -p -D -m 755 etc/init.d/vsm-physical %{buildroot}%{_initrddir}/vsm-physical
install -p -D -m 755 etc/init.d/vsm-agent %{buildroot}%{_initrddir}/vsm-agent
install -p -D -m 755 etc/init.d/vsm-api %{buildroot}%{_initrddir}/vsm-api
install -p -D -m 755 etc/init.d/vsm-conductor %{buildroot}%{_initrddir}/vsm-conductor
install -p -D -m 755 etc/init.d/vsm-scheduler %{buildroot}%{_initrddir}/vsm-scheduler
%endif


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

%if 0%{?suse_version}
install -p -D -m 755 bin/cluster_manifest %{buildroot}%{_usr}/bin/cluster_manifest
install -p -D -m 755 bin/server_manifest  %{buildroot}%{_usr}/bin/server_manifest
install -p -D -m 755 bin/refresh-osd-status %{buildroot}%{_usr}/bin/refresh-osd-status
install -p -D -m 755 bin/refresh-cluster-status %{buildroot}%{_usr}/bin/refresh-cluster-status
install -p -D -m 755 bin/getip  %{buildroot}%{_usr}/bin/getip
install -p -D -m 755 bin/import_ceph_conf  %{buildroot}%{_usr}/bin/import_ceph_conf
install -p -D -m 755 bin/get_smart_info %{buildroot}%{_bindir}/get_smart_info

install -p -D -m 755 tools/get_storage %{buildroot}%{_usr}/bin/get_storage
install -p -D -m 644 tools/spot_info_list %{buildroot}%{_usr}/bin/spot_info_list
install -p -D -m 755 tools/vsm-reporter.py %{buildroot}%{_usr}/bin/vsm-reporter
install -p -D -m 755 bin/intergrate-cluster %{buildroot}%{_usr}/bin/intergrate-cluster
%else
install -p -D -m 755 bin/cluster_manifest %{buildroot}%{_usr}/local/bin/cluster_manifest
install -p -D -m 755 bin/server_manifest  %{buildroot}%{_usr}/local/bin/server_manifest
install -p -D -m 755 bin/refresh-osd-status %{buildroot}%{_usr}/local/bin/refresh-osd-status
install -p -D -m 755 bin/refresh-cluster-status %{buildroot}%{_usr}/local/bin/refresh-cluster-status
install -p -D -m 755 bin/getip  %{buildroot}%{_usr}/local/bin/getip
install -p -D -m 755 bin/import_ceph_conf  %{buildroot}%{_usr}/local/bin/import_ceph_conf
install -p -D -m 755 bin/get_smart_info %{buildroot}%{_bindir}/get_smart_info

install -p -D -m 755 tools/get_storage %{buildroot}%{_usr}/local/bin/get_storage
install -p -D -m 755 tools/spot_info_list %{buildroot}%{_usr}/local/bin/spot_info_list
install -p -D -m 755 tools/vsm-reporter.py %{buildroot}%{_usr}/local/bin/vsm-reporter
install -p -D -m 755 bin/intergrate-cluster %{buildroot}%{_usr}/local/bin/intergrate-cluster
%endif

%if 0%{?suse_version}
%fdupes %{buildroot}
%endif

%pre
getent group vsm >/dev/null || groupadd -r vsm --gid 165
if ! getent passwd vsm >/dev/null; then
  useradd -u 165 -r -g vsm -G vsm,nobody -d %{_sharedstatedir}/vsm -s /sbin/nologin -c "Vsm Storage Services" vsm
fi
%if 0%{?suse_version}
%service_add_pre vsm-physical.service vsm-agent.service vsm-api.service vsm-scheduler.service vsm-conductor.service
install -d -m 755 %{buildroot}/var/run/vsm
%else
mkdir -p /var/run/vsm/
mkdir -p /var/log/vsm/
mkdir -p /var/lib/vsm
mkdir -p /etc/vsm/
mkdir -p /etc/vsm/rootwrap.d
chown -R vsm /var/run/vsm
chown -R vsm /var/log/vsm/
chown -R vsm /var/lib/vsm
chown -R vsm /etc/vsm/
%endif
if [ -f /etc/init.d/ceph ]; then
    sed -i 's,do_cmd.* 30 $BINDIR.*,do_cmd "timeout 30 $BINDIR/ceph -c $conf --name=osd.$id --keyring=$osd_keyring osd crush create-or-move -- $id ${osd_weight:-${defaultweight:-1}} $osd_location ||:",g' /etc/init.d/ceph;
    sed -i 's,do_cmd.* 30 $BINDIR.*,do_cmd "timeout 30 $BINDIR/ceph -c $conf --name=osd.$id --keyring=$osd_keyring osd crush create-or-move -- $id ${osd_weight:-${defaultweight:-1}} $osd_location ||:",g' /etc/init.d/ceph;

fi

exit 0

%post
%if 0%{?suse_version}
%service_add_post vsm-physical.service vsm-agent.service vsm-api.service vsm-scheduler.service vsm-conductor.service
%endif

%preun
%if 0%{?suse_version}
%service_del_preun vsm-physical.service vsm-agent.service vsm-api.service vsm-scheduler.service vsm-conductor.service
%endif

%postun
%if 0%{?suse_version}
%service_del_postun vsm-physical.service vsm-agent.service vsm-api.service vsm-scheduler.service vsm-conductor.service
%endif


%files
%defattr(-,root,root,-)
%doc LICENSE doc
%{python_sitelib}/*


%dir %{_sysconfdir}/logrotate.d
%if 0%{?suse_version}
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/logrotate.d/vsm
%dir %attr(-, root, root) /var/log/vsm
%dir %attr(-, root, root) /var/lib/vsm
##%%dir %%attr(-, root, root) /var/run/vsm
%dir %attr(-, root, root) /etc/vsm
%dir %attr(-, root, root) /etc/vsm/rootwrap.d
%dir %{_sysconfdir}/vsm
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/vsm/vsm.conf
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/vsm/ceph.conf.template
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/vsm/api-paste.ini
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/vsm/rootwrap.conf
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/vsm/policy.json
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/vsm/logging.conf
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/vsm/cache-tier.conf
%dir %{_sysconfdir}/vsm/rootwrap.d
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/vsm/rootwrap.d/vsm.filters

%dir %{_sysconfdir}/sudoers.d
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/sudoers.d/vsm
%else
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/logrotate.d/vsmceph
%dir %attr(-, vsm, vsm) /var/log/vsm
%dir %attr(-, vsm, vsm) /var/lib/vsm
%dir %attr(-, vsm, vsm) /etc/vsm
%dir %attr(-, vsm, vsm) /etc/vsm/rootwrap.d
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

%dir %{_sysconfdir}/sudoers.d
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/sudoers.d/vsm
%endif


%if 0%{?suse_version}
%dir %{_unitdir}
%attr(-, root, root) %{_unitdir}/vsm-physical.service
%attr(-, root, root) %{_unitdir}/vsm-agent.service
%attr(-, root, root) %{_unitdir}/vsm-api.service
%attr(-, root, root) %{_unitdir}/vsm-conductor.service
%attr(-, root, root) %{_unitdir}/vsm-scheduler.service
%attr(-, root, root) %{_sbindir}/rcvsm-physical
%attr(-, root, root) %{_sbindir}/rcvsm-agent
%attr(-, root, root) %{_sbindir}/rcvsm-api
%attr(-, root, root) %{_sbindir}/rcvsm-conductor
%attr(-, root, root) %{_sbindir}/rcvsm-scheduler
%dir %{_tmpfilesdir}
%{_tmpfilesdir}/%{name}.conf
%else
%dir %{_initrddir}
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-physical
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-agent
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-api
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-conductor
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-scheduler
%endif


%if 0%{?suse_version}
%attr(-, root, root) %{_bindir}/vsm-rootwrap
%attr(-, root, root) %{_bindir}/vsm-physical
%attr(-, root, root) %{_bindir}/vsm-agent
%attr(-, root, root) %{_bindir}/vsm-api
%attr(-, root, root) %{_bindir}/vsm-conductor
%attr(-, root, root) %{_bindir}/vsm-all
%attr(-, root, root) %{_bindir}/vsm-manage
%attr(-, root, root) %{_bindir}/vsm-scheduler
%attr(-, root, root) %{_bindir}/key
%attr(-, root, root) %{_bindir}/auto_key_gen
%attr(-, root, root) %{_bindir}/vsm-assist
%attr(-, root, root) %{_bindir}/presentpool
%attr(-, root, root) %{_bindir}/rbd_ls
%attr(-, root, root) %{_bindir}/agent-token
%attr(-, root, root) %{_bindir}/admin-token
%attr(-, root, root) %{_bindir}/vsm-backup
%attr(-, root, root) %{_bindir}/vsm-restore
%attr(-, root, root) %{_bindir}/get_smart_info
%attr(-, root, root) %{_bindir}/intergrate-cluster
%attr(-, root, root) %{_usr}/bin/import_ceph_conf

%attr(-, root, root) %{_usr}/bin/getip
%attr(-, root, root) %{_usr}/bin/cluster_manifest
%attr(-, root, root) %{_usr}/bin/server_manifest
%attr(-, root, root) %{_usr}/bin/refresh-osd-status
%attr(-, root, root) %{_usr}/bin/refresh-cluster-status

%attr(-, root, root) %{_usr}/bin/get_storage
%attr(-, root, root) %{_usr}/bin/spot_info_list
%attr(-, root, root) %{_usr}/bin/vsm-reporter
%else
%dir %{_bindir}
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

%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/getip
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/cluster_manifest
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/server_manifest
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/refresh-osd-status
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/refresh-cluster-status

%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/get_storage
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/spot_info_list
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/vsm-reporter
%endif

#-----------------------------
# Prepools
#-----------------------------
%dir %{_sysconfdir}/vsm/prepools
%if 0%{?suse_version}
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/vsm/prepools/*
%else
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/prepools/*
%endif
# TODO check this line whether needed
