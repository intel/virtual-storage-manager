%global with_doc %{!?_without_doc:1}%{?_without_doc:0}
%define version %{getenv:VERSION}
%define release %{getenv:RELEASE}

Name:             vsm-deploy
Version:          %{version}
Release:          %{release}
Summary:          Deployment tool for VSM

Group:            Deploy/VSM
License:          Intel
URL:              http://intel.com
Source:           %{name}-%{version}.tar.gz
BuildArch:        noarch
%if 0%{?suse_version}
BuildRequires:    shadow
Requires:         shadow
%endif

#TODO Add ceph rpms.
%description
Intel VSM Storage System Tools Kit.

%if 0%{?with_doc}
%package doc
Summary:          Documentation for VSM Deploy Tools Kit.
Group:            Documentation

%description      doc
OpenStack Tools Kit (codename VSM) provides services to manage and
access block storage services for use by Virtual Machine instances.

This package contains documentation files for vsm.
%endif

%prep
%setup -q -n %{name}-%{version}

%build


%install
#---------------------------
# usr/bin/
#---------------------------
install -d -m 755 %{buildroot}%{_sysconfdir}/manifest/
install -p -D -m 755 tools/etc/vsm/cluster.manifest %{buildroot}%{_sysconfdir}/manifest/cluster.manifest
install -p -D -m 755 tools/etc/vsm/server.manifest %{buildroot}%{_sysconfdir}/manifest/server.manifest

install -d -m 755 %{buildroot}%{_usr}/local/bin/
install -d -m 755 %{buildroot}%{_usr}/local/bin/tools

%if 0%{?suse_version}
install -p -D -m 755 usr/bin/vsm-controller %{buildroot}%{_usr}/bin/vsm-controller
install -p -D -m 755 usr/bin/vsm-storage %{buildroot}%{_usr}/bin/vsm-storage
install -p -D -m 755 usr/bin/populate-servermanifest %{buildroot}%{_usr}/bin/populate-servermanifest
install -p -D -m 755 usr/bin/partition-drives %{buildroot}%{_usr}/bin/partition-drives
install -p -D -m 755 usr/bin/vsm-installer %{buildroot}%{_usr}/bin/vsm-installer
install -p -D -m 755 usr/bin/vsm-node %{buildroot}%{_usr}/bin/vsm-node
install -d -m 755 %{buildroot}%{_sysconfdir}/systemd/system
install -p -D -m 755 etc/systemd/system/epmd.socket %{buildroot}%{_sysconfdir}/systemd/system
install -p -D -m 755 restart-all %{buildroot}%{_usr}/bin/restart-all
install -p -D -m 755 sync-code %{buildroot}%{_usr}/bin/sync-code
install -p -D -m 755 replace-str %{buildroot}%{_usr}/bin/replace-str

install -p -D -m 755 clean-data %{buildroot}%{_usr}/bin/clean-data
install -p -D -m 755 __clean-data %{buildroot}%{_usr}/bin/__clean-data
install -p -D -m 755 downloadrepo  %{buildroot}%{_usr}/bin/downloadrepo
install -p -D -m 755 start_osd %{buildroot}%{_usr}/bin/start_osd
install -p -D -m 755 ec-profile %{buildroot}%{_usr}/bin/ec-profile
install -p -D -m 755 cache-tier-defaults %{buildroot}%{_usr}/bin/cache-tier-defaults
install -p -D -m 755 reset_status %{buildroot}%{_usr}/bin/reset_status
install -p -D -m 755 vsm-update %{buildroot}%{_usr}/bin/vsm-update

install -p -D -m 755 vsm-checker %{buildroot}%{_usr}/bin/vsm-checker
install -d -m 755 %{buildroot}%{_usr}/lib/vsm
cp -rf keys  %{buildroot}%{_usr}/lib/vsm/
cp -rf tools/ %{buildroot}%{_usr}/lib/vsm/
cp -rf usr/bin/keys  %{buildroot}%{_usr}/lib/vsm/
cp -rf usr/bin/tools/ %{buildroot}%{_usr}/lib/vsm/
%else
install -p -D -m 755 vsm-controller %{buildroot}%{_usr}/local/bin/vsm-controller
install -p -D -m 755 vsm-installer %{buildroot}%{_usr}/local/bin/vsm-installer
install -p -D -m 755 vsm-node %{buildroot}%{_usr}/local/bin/vsm-node
install -p -D -m 755 restart-all %{buildroot}%{_usr}/local/bin/restart-all
install -p -D -m 755 sync-code %{buildroot}%{_usr}/local/bin/sync-code
install -p -D -m 755 replace-str %{buildroot}%{_usr}/local/bin/replace-str

install -p -D -m 755 clean-data %{buildroot}%{_usr}/local/bin/clean-data
install -p -D -m 755 __clean-data %{buildroot}%{_usr}/local/bin/__clean-data
install -p -D -m 755 downloadrepo  %{buildroot}%{_usr}/local/bin/downloadrepo
install -p -D -m 755 preinstall %{buildroot}%{_usr}/local/bin/preinstall
install -p -D -m 755 rpms_list %{buildroot}%{_usr}/local/bin/rpms_list
install -p -D -m 755 start_osd %{buildroot}%{_usr}/local/bin/start_osd
install -p -D -m 755 ec-profile %{buildroot}%{_usr}/local/bin/ec-profile
install -p -D -m 755 cache-tier-defaults %{buildroot}%{_usr}/local/bin/cache-tier-defaults
install -p -D -m 755 reset_status %{buildroot}%{_usr}/local/bin/reset_status
install -p -D -m 755 vsm-update %{buildroot}%{_usr}/local/bin/vsm-update

install -p -D -m 755 rpm.lst %{buildroot}%{_usr}/local/bin/rpm.lst
install -p -D -m 755 vsm-checker %{buildroot}%{_usr}/local/bin/vsm-checker

cp -rf keys  %{buildroot}%{_usr}/local/bin/
cp -rf tools %{buildroot}%{_usr}/local/bin/
%endif


%pre
getent group vsm >/dev/null || groupadd -r vsm --gid 165
if ! getent passwd vsm >/dev/null; then
  useradd -u 165 -r -g vsm -G vsm,nobody -d %{_sharedstatedir}/vsm -s /sbin/nologin -c "Vsm Storage Services" vsm
fi
exit 0

%files
%defattr(-,root,root,-)
%if 0%{?suse_version}
%dir %{_sysconfdir}/systemd
%dir %{_sysconfdir}/systemd/system
%attr(-, root, root) %{_usr}/bin/vsm-storage
%attr(-, root, root) %{_usr}/bin/partition-drives
%attr(-, root, root) %{_usr}/bin/populate-servermanifest
%attr(-, root, root) %{_usr}/bin/vsm-controller
%attr(-, root, root) %{_usr}/bin/restart-all
%attr(-, root, root) %{_usr}/bin/replace-str
%attr(-, root, root) %{_usr}/bin/sync-code
%attr(-, root, root) %{_usr}/bin/vsm-node
%attr(-, root, root) %{_usr}/bin/clean-data
%attr(-, root, root) %{_usr}/bin/__clean-data
%attr(-, root, root) %{_usr}/bin/vsm-installer
%attr(-, root, root) %{_usr}/bin/downloadrepo
%attr(-, root, root) %{_usr}/bin/start_osd
%attr(-, root, root) %{_usr}/bin/ec-profile
%attr(-, root, root) %{_usr}/bin/cache-tier-defaults
%attr(-, root, root) %{_usr}/bin/reset_status
%attr(-, root, root) %{_usr}/bin/vsm-update
%attr(-, root, root) %{_usr}/bin/vsm-checker
%dir %{_usr}/lib/vsm
%attr(-, root, root) %{_usr}/lib/vsm/*
%dir %{_usr}/lib/vsm/keys
%attr(-, root, root) %{_usr}/lib/vsm/keys/*

%dir %{_sysconfdir}/manifest
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/manifest/server.manifest
%config(noreplace) %attr(-, root, root) %{_sysconfdir}/manifest/cluster.manifest
%{_sysconfdir}/systemd/system/epmd.socket
%else
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/vsm-controller
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/restart-all
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/replace-str
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/sync-code
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/vsm-node
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/clean-data
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/__clean-data
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/vsm-installer
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/downloadrepo
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/preinstall
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/rpms_list
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/start_osd
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/ec-profile
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/cache-tier-defaults
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/reset_status
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/vsm-update

%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/rpm.lst
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/vsm-checker

%dir %{_usr}/local/bin/keys
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/keys/*

%dir %{_usr}/local/bin/tools
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/tools/*

%dir %{_sysconfdir}/manifest
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/manifest/server.manifest
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/manifest/cluster.manifest
%endif

