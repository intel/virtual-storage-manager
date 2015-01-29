%global with_doc %{!?_without_doc:1}%{?_without_doc:0}

Name:             vsm-deploy
Version:          2015.01
Release:          1.0%{?dist}
Summary:          VSM-Deploy

Group:            Deploy/VSM
License:          Intel
URL:              http://intel.com
Source0:          vsm-deploy-%{version}.tar.gz
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
%setup -q -n vsm-deploy-%{version}

%build

mkdir -p %{buildroot}

%install
#---------------------------
# usr/bin/
#---------------------------
install -d -m 755 %{buildroot}%{_sysconfdir}/manifest/
install -p -D -m 755 tools/etc/vsm/cluster.manifest %{buildroot}%{_sysconfdir}/manifest/cluster.manifest
install -p -D -m 755 tools/etc/vsm/server.manifest %{buildroot}%{_sysconfdir}/manifest/server.manifest

install -d -m 755 %{buildroot}%{_usr}/local/bin/
install -d -m 755 %{buildroot}%{_usr}/local/bin/tools

install -p -D -m 755 vsm-controller %{buildroot}%{_usr}/local/bin/vsm-controller
install -p -D -m 755 restart-all %{buildroot}%{_usr}/local/bin/restart-all
install -p -D -m 755 sync-code %{buildroot}%{_usr}/local/bin/sync-code
install -p -D -m 755 replace-str %{buildroot}%{_usr}/local/bin/replace-str

install -p -D -m 755 vsm-node %{buildroot}%{_usr}/local/bin/vsm-node
install -p -D -m 755 clean-data %{buildroot}%{_usr}/local/bin/clean-data
install -p -D -m 755 __clean-data %{buildroot}%{_usr}/local/bin/__clean-data
install -p -D -m 755 vsm-installer %{buildroot}%{_usr}/local/bin/vsm-installer
install -p -D -m 755 downloadrepo  %{buildroot}%{_usr}/local/bin/downloadrepo
install -p -D -m 755 preinstall %{buildroot}%{_usr}/local/bin/preinstall
install -p -D -m 755 rpms_list %{buildroot}%{_usr}/local/bin/rpms_list
install -p -D -m 755 start_osd %{buildroot}%{_usr}/local/bin/start_osd
install -p -D -m 755 ec-profile %{buildroot}%{_usr}/local/bin/ec-profile
install -p -D -m 755 cache-tier-defaults %{buildroot}%{_usr}/local/bin/cache-tier-defaults
install -p -D -m 755 reset_status %{buildroot}%{_usr}/local/bin/reset_status
install -p -D -m 755 vsm-update %{buildroot}%{_usr}/local/bin/vsm-update

cp -rf keys  %{buildroot}%{_usr}/local/bin/
cp -rf tools %{buildroot}%{_usr}/local/bin/

%pre
getent group vsm >/dev/null || groupadd -r vsm --gid 165
if ! getent passwd vsm >/dev/null; then
  useradd -u 165 -r -g vsm -G vsm,nobody -d %{_sharedstatedir}/vsm -s /sbin/nologin -c "Vsm Storage Services" vsm
fi
exit 0

%files
%defattr(-,root,root,-)
%dir %{_usr}
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

%dir %{_usr}/local/bin/keys
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/keys/*

%dir %{_usr}/local/bin/tools
%config(noreplace) %attr(-, root, vsm) %{_usr}/local/bin/tools/*

%dir %{_sysconfdir}/manifest
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/manifest/server.manifest
%config(noreplace) %attr(-, root, vsm) %{_sysconfdir}/manifest/cluster.manifest

%changelog
* Mon Feb 17 2014 Ji You <ji.you@intel.com> - 2014.2.17-2
- Initial release
