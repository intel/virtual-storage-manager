%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           vsm-dashboard
Version:	    2015.01
Release:	    1.0%{?dist}
Url:            http://intel.com/itflex
License:        Apache 2.0
Group:          Development/Languages/Python
Source:		    %{name}-%{version}.tar.gz
BuildRoot:	    %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Summary:        web based management interface for VSM.

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-setuptools
BuildRequires:  MySQL-python
BuildRequires:  python-django-compressor
BuildRequires:  Django14
BuildRequires:  python-django-openstack-auth
BuildRequires:  python-netaddr
BuildRequires:  python-keystoneclient
BuildRequires:  pytz
BuildRequires:  python-lockfile

Requires:    Django14
Requires:    apr
Requires:    apr-util
Requires:    apr-util-ldap
Requires:    httpd
Requires:    httpd-tools
Requires:    mod_wsgi
Requires:    pyparsing
Requires:    python-argparse
Requires:    python-backports
Requires:    python-backports-ssl_match_hostname
Requires:    python-chardet
Requires:    python-cliff
Requires:    python-cmd2
Requires:    python-django-appconf
Requires:    python-django-compressor
Requires:    python-django-horizon
Requires:    python-django-openstack-auth
Requires:    python-httplib2
Requires:    python-iso8601
Requires:    python-jsonschema
Requires:    python-keyring
Requires:    python-keystoneclient
Requires:    python-ordereddict
Requires:    python-oslo-config
Requires:    python-prettytable
Requires:    python-requests
Requires:    python-simplejson
Requires:    python-six
Requires:    python-urllib3
Requires:    python-versiontools
Requires:    python-warlock
Requires:    python-webob
Requires:    python-vsmclient

%description
The VSM Dashboard is a reference implementation of a Django site that
uses the Django project to provide web based interactions with the
VSM cloud controller.

%prep
%setup -q -n %{name}-%{version}

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
#---------------------------
# httpd Configuration file
#---------------------------

install -d -m 755 %{buildroot}%{_sysconfdir}/httpd/conf.d
install -p -D -m 755 tools/vsm-dashboard.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/vsm-dashboard.conf


#---------------------------
# bin Files for lessc
#---------------------------

install -d -m 755 %{buildroot}%{_bindir}
install -p -D -m 755 bin/less/lessc %{buildroot}%{_bindir}/
cp -av bin/lib/ %{buildroot}%{_libdir}/


#---------------------------
# Source files.
#---------------------------

install -d -m 755 %{buildroot}%{_datadir}/vsm-dashboard
cp -av vsm_dashboard %{buildroot}%{_datadir}/vsm-dashboard/
cp -av static %{buildroot}%{_datadir}/vsm-dashboard/
install -p -D -m 755 manage.py %{buildroot}%{_datadir}/vsm-dashboard/

#---------------------------
# configuration file
#---------------------------

#install -d -m 755 %{buildroot}%{_sysconfdir}/vsm-dashboard/
#ln -sf %{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py %{_sysconfdir}/vsm-dashboard/local_settings
#rm -rf %{buildroot}%{_sysconfdir}/vsm-dashboard/local_settings
#ln -sf %{buildroot}%{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py %{buildroot}%{_sysconfdir}/vsm-dashboard/local_settings

%clean
%{__rm} -rf %{buildroot}

%post
#python -m dashboard.manage syncdb

mkdir -p %{_sysconfdir}/vsm-dashboard
chown -R apache:apache %{_sysconfdir}/vsm-dashboard
rm -rf %{_sysconfdir}/vsm-dashboard/*
ln -sf %{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py %{_sysconfdir}/vsm-dashboard/local_settings

chmod -R a+r %{_datadir}/vsm-dashboard
chown -R apache:apache %{_datadir}/vsm-dashboard
chown -R apache:apache %{_sysconfdir}/vsm-dashboard
chown -R apache:apache %{_sysconfdir}/httpd/conf.d/vsm-dashboard.conf

VSM_VERSION=%{version}-%{release}
sed -i "s,%VSM_VERSION%,$VSM_VERSION,g" %{_datadir}/vsm-dashboard/vsm_dashboard/dashboards/vsm/overview/summarys.py

%files
%defattr(-,root,root,-)
%dir %{_sysconfdir}/httpd/conf.d
%config(noreplace) %attr(-, root, apache) %{_sysconfdir}/httpd/conf.d/vsm-dashboard.conf

%dir %{_bindir}
%config(noreplace) %attr(-, root, apache) %{_bindir}/lessc

%dir %attr(0755, apache, apache) %{_libdir}/less
%{_libdir}/less/*

%dir %attr(0755, apache, apache) %{_datadir}/vsm-dashboard
%{_datadir}/vsm-dashboard/*
%config(noreplace) %attr(-, apache, apache) %{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py
#%dir %attr(0755, apache, apache) %{_datadir}/vsm-dashboard/vsm_dashboard
#%{_datadir}/vsm-dashboard/vsm_dashboard/*

#%dir %attr(0755, apache, apache) %{_datadir}/vsm-dashboard/static
#%{_datadir}/vsm-dashboard/static/*
#%config(noreplace) %attr(-, root, apache) %{_datadir}/vsm-dashboard/manage.py

#%dir %attr(0755, apache, apache) %{_sysconfdir}/vsm-dashboard/
#%config(noreplace) %attr(-, root, apache) %{_sysconfdir}/vsm-dashboard/local_settings

#%{_sysconfdir}/vsm-dashboard/*

%changelog
* Mon Feb 17 2014 Ji You <ji.you@intel.com> - 2014.2.17-2
- Initial release
