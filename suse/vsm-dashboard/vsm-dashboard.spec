%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           vsm-dashboard
Version:	    2015.01
Release:	    1.0%{?dist}
Url:            http://intel.com/itflex
License:        Apache 2.0
Group:          Development/Languages/Python
Source:		    %{name}-%{version}.tar.gz
BuildRoot:	    %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Summary:        Web based management interface for VSM

ExclusiveArch:  x86_64 i586
BuildRequires:    python-MySQL-python
BuildRequires:    python-django_compressor
BuildRequires:    python-Django
BuildRequires:    python-django_openstack_auth
BuildRequires:    python-pytz

BuildRequires:  python-devel
BuildRequires:  python-setuptools
BuildRequires:  python-netaddr
BuildRequires:  python-keystoneclient
BuildRequires:  python-lockfile

Requires:    apache2
Requires:    python-Django
Requires:    python-django_openstack_auth
Requires:    python-django_compressor

Requires:    libapr-util1
Requires:    apache2
Requires:    mod_wsgi
Requires:    python-pyparsing
Requires:    python-argparse
Requires:    python-backports.ssl_match_hostname
Requires:    python-chardet
Requires:    python-cliff
Requires:    python-cmd2
Requires:    python-django-appconf
Requires:    python-horizon
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

install -d -m 755 %{buildroot}%{_sysconfdir}/apache2/conf.d
install -p -D -m 755 etc/apache2/conf.d/vsm-dashboard.conf %{buildroot}%{_sysconfdir}/apache2/conf.d/vsm-dashboard.conf


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

install -p -D -m 755 usr/share/vsm-dashboard/vsm_dashboard/local/local_settings.py %{buildroot}%{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py

#---------------------------
# configuration file
#---------------------------


%clean
%{__rm} -rf %{buildroot}

%post
#python -m dashboard.manage syncdb

mkdir -p %{_sysconfdir}/vsm-dashboard

chown -R wwwrun:www %{_sysconfdir}/vsm-dashboard
rm -rf %{_sysconfdir}/vsm-dashboard/*
ln -sf %{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py %{_sysconfdir}/vsm-dashboard/local_settings

chmod -R a+r %{_datadir}/vsm-dashboard


chown -R wwwrun:www %{_datadir}/vsm-dashboard
chown -R wwwrun:www %{_sysconfdir}/vsm-dashboard

chown -R wwwrun:www %{_sysconfdir}/apache2/conf.d/vsm-dashboard.conf

VSM_VERSION=%{version}-%{release}
sed -i "s,%VSM_VERSION%,$VSM_VERSION,g" %{_datadir}/vsm-dashboard/vsm_dashboard/dashboards/vsm/overview/summarys.py

%files
%defattr(-,root,root,-)
%dir %{_sysconfdir}/apache2
%dir %{_sysconfdir}/apache2/conf.d
%config(noreplace) %attr(-, root, www) %{_sysconfdir}/apache2/conf.d/vsm-dashboard.conf

%dir %{_bindir}
%config(noreplace) %attr(-, root, www) %{_bindir}/lessc


%dir %attr(0755, wwwrun, www) %{_libdir}/less
%{_libdir}/less/*

%dir %attr(0755, wwwrun, www) %{_datadir}/vsm-dashboard
%{_datadir}/vsm-dashboard/*


%config(noreplace) %attr(-, wwwrun, www) %{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py

%changelog
* Mon Feb 17 2014 Ji You <ji.you@intel.com> - 2014.2.17-2
- Initial release
