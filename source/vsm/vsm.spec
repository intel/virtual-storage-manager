%global with_doc %{!?_without_doc:1}%{?_without_doc:0}

Name:             vsm
Version:          2014.11
Release:          0.8.0%{?dist}
Summary:          VSM

Group:            Storage/System
License:          Intel
URL:              http://intel.com
Source0:          vsm-%{version}.tar.gz

BuildArch:        noarch
BuildRequires:    MySQL-python
BuildRequires:    python-importlib
BuildRequires:    python-ordereddict
BuildRequires:    python-pbr
BuildRequires:    python-decorator
BuildRequires:    python-tempita
BuildRequires:    python-sqlalchemy0.7
BuildRequires:    python-amqplib
BuildRequires:    python-anyjson
BuildRequires:    python-argparse
BuildRequires:    python-eventlet
BuildRequires:    python-kombu
BuildRequires:    python-lockfile
BuildRequires:    python-lxml
BuildRequires:    python-routes1.12
BuildRequires:    python-webob
BuildRequires:    python-greenlet
BuildRequires:    python-paste-deploy1.5
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
Requires:    python-importlib
Requires:    python-ordereddict
Requires:    python-pbr
Requires:    python-decorator
Requires:    python-tempita
Requires:    python-sqlalchemy0.7
Requires:    python-amqplib
Requires:    python-anyjson
Requires:    python-argparse
Requires:    python-eventlet
Requires:    python-kombu
Requires:    python-lockfile
Requires:    python-lxml
Requires:    python-routes1.12
Requires:    python-webob
Requires:    python-greenlet
Requires:    python-paste-deploy1.5
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
Intel VSM Storage System.

%if 0%{?with_doc}
%package doc
Summary:          Documentation for OpenStack Volume
Group:            Documentation

Requires:         %{name} = %{version}-%{release}
BuildRequires:    graphviz
BuildRequires:    python-eventlet
BuildRequires:    python-routes
BuildRequires:    python-sqlalchemy0.7
BuildRequires:    python-webob
BuildRequires:    python-migrate
BuildRequires:    python-iso8601

%description      doc
OpenStack Volume (codename Cinder) provides services to manage and
access block storage volumes for use by Virtual Machine instances.

This package contains documentation files for vsm.
%endif

%prep
%setup -q -n vsm-%{version}
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
install -p -D -m 640 etc/sudoers.d/vsm %{buildroot}%{_sysconfdir}/sudoers.d/vsm
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
install -p -D -m 755 bin/vsm-rootwrap %{buildroot}%{_bindir}/vsm-rootwrap
install -p -D -m 755 bin/vsm-conductor %{buildroot}%{_bindir}/vsm-conductor
install -p -D -m 755 bin/vsm-scheduler %{buildroot}%{_bindir}/vsm-scheduler
install -p -D -m 755 bin/vsm-rootwrap %{buildroot}%{_bindir}/vsm-rootwrap
install -p -D -m 755 bin/key %{buildroot}%{_bindir}/key
install -p -D -m 755 bin/auto_key_gen %{buildroot}%{_bindir}/auto_key_gen
install -p -D -m 755 bin/vsm-assist %{buildroot}%{_bindir}/vsm-assist
install -p -D -m 755 bin/presentpool %{buildroot}%{_bindir}/presentpool
install -p -D -m 755 bin/rbd_ls %{buildroot}%{_bindir}/rbd_ls
install -p -D -m 755 bin/agent-token %{buildroot}%{_bindir}/agent-token
install -p -D -m 755 bin/vsm-backup %{buildroot}%{_bindir}/vsm-backup
install -p -D -m 755 bin/vsm-restore %{buildroot}%{_bindir}/vsm-restore
install -p -D -m 755 bin/cluster_manifest %{buildroot}%{_usr}/local/bin/cluster_manifest
install -p -D -m 755 bin/server_manifest  %{buildroot}%{_usr}/local/bin/server_manifest
install -p -D -m 755 bin/getip  %{buildroot}%{_usr}/local/bin/getip


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
chown -R vsm /etc/vsm/
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

%dir %{_sysconfdir}/vsm
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/vsm.conf
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/ceph.conf.template
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/api-paste.ini
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/rootwrap.conf
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/policy.json
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/logging.conf
%dir %{_sysconfdir}/vsm/rootwrap.d
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/rootwrap.d/vsm.filters

%dir %{_sysconfdir}/sudoers.d
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/sudoers.d/vsm

%dir %{_initrddir}
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-physical
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-agent
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-api
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-conductor
%config(noreplace) %attr(-, root, vsm) %{_initrddir}/vsm-scheduler

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
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-backup
%config(noreplace) %attr(-, root, vsm) %{_bindir}/vsm-restore


%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/getip
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/cluster_manifest
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/server_manifest
#-----------------------------
# Prepools
#-----------------------------
%dir %{_sysconfdir}/vsm/prepools
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/vsm/prepools/*
# TODO check this line whether needed

%changelog
* Mon Feb 17 2014 Ji You <ji.you@intel.com> - 2014.2.17-2
- Initial release
