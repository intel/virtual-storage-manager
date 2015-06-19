%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%define version %{getenv:VERSION}
%define release %{getenv:RELEASE}

Name:           vsm-dashboard
Version:        %{version}
Release:        %{release}
Url:            http://intel.com/itflex
License:        Apache-2.0
Group:          Development/Languages/Python
Source:         %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Summary:        Web based management interface for VSM

ExclusiveArch:  x86_64 i586
%if 0%{?suse_version}
BuildRequires:    python-MySQL-python
BuildRequires:    python-django_compressor
BuildRequires:    python-Django
BuildRequires:    python-django_openstack_auth
BuildRequires:    python-pytz
BuildRequires:    fdupes
%else
BuildRequires:  MySQL-python
BuildRequires:  python-django-compressor
BuildRequires:  Django14
BuildRequires:  python-django-openstack-auth
BuildRequires:  pytz
%endif

BuildRequires:  python-devel
BuildRequires:  python-setuptools
BuildRequires:  python-netaddr
BuildRequires:  python-keystoneclient
BuildRequires:  python-lockfile

%if 0%{?suse_version}
Requires:    apache2
Requires:    python-Django = 1.6.11
Requires:    python-django_openstack_auth
Requires:    python-django_compressor
#Requires:    libapr-util1
Requires:    apache2
Requires:    python-pyparsing
Requires:    python-backports.ssl_match_hostname
Requires:    python-horizon
%else
Requires:    Django14
Requires:    python-django-openstack-auth
Requires:    python-django-compressor

Requires:    apr
Requires:    apr-util
Requires:    apr-util-ldap
Requires:    httpd
Requires:    httpd-tools
Requires:    pyparsing
Requires:    python-backports
Requires:    python-backports-ssl_match_hostname
Requires:    python-django-horizon
Requires:    python-httplib2
Requires:    python-urllib3
%endif
Requires:    mod_wsgi
Requires:    python-argparse
Requires:    python-chardet
Requires:    python-cliff
Requires:    python-cmd2
Requires:    python-django-appconf
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

%if 0%{?suse_version}
install -d -m 755 %{buildroot}%{_sysconfdir}/apache2/conf.d
install -p -D -m 755 etc/apache2/conf.d/vsm-dashboard.conf %{buildroot}%{_sysconfdir}/apache2/conf.d/vsm-dashboard.conf
install -p -D -m 755 etc/apache2/default-server-ssl.conf %{buildroot}%{_sysconfdir}/apache2/default-server-ssl.conf
install -p -D -m 755 usr/share/vsm-dashboard/vsm_dashboard/local/local_settings.py %{buildroot}%{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py
%else
install -d -m 755 %{buildroot}%{_sysconfdir}/httpd/conf.d
install -p -D -m 755 tools/vsm-dashboard.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/vsm-dashboard.conf
%endif


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

#install -d -m 755 %%{buildroot}%%{_sysconfdir}/vsm-dashboard/
#ln -sf %%{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py %%{_sysconfdir}/vsm-dashboard/local_settings
#rm -rf %%{buildroot}%%{_sysconfdir}/vsm-dashboard/local_settings
#ln -sf %%{buildroot}%%{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py %%{buildroot}%%{_sysconfdir}/vsm-dashboard/local_settings

%if 0%{?suse_version}
#ln -sf %{_datadir}/vsm-dashboard/static/dashboard/img %{buildroot}%{_datadir}/vsm-dashboard/vsm_dashboard/static/dashboard/
%fdupes %{buildroot}
%endif

%clean
%{__rm} -rf %{buildroot}

%post
#python -m dashboard.manage syncdb

mkdir -p %{_sysconfdir}/vsm-dashboard

%if 0%{?suse_version}
chown -R wwwrun:www %{_sysconfdir}/vsm-dashboard
%else
chown -R apache:apache %{_sysconfdir}/vsm-dashboard
%endif
rm -rf %{_sysconfdir}/vsm-dashboard/*
ln -sf %{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py %{_sysconfdir}/vsm-dashboard/local_settings

chmod -R a+r %{_datadir}/vsm-dashboard


%if 0%{?suse_version}
chown -R wwwrun:www %{_datadir}/vsm-dashboard
chown -R wwwrun:www %{_sysconfdir}/vsm-dashboard
%else
chown -R apache:apache %{_datadir}/vsm-dashboard
chown -R apache:apache %{_sysconfdir}/vsm-dashboard
%endif


%if 0%{?suse_version}
chown -R wwwrun:www %{_sysconfdir}/apache2/conf.d/vsm-dashboard.conf
chown -R wwwrun:www %{_sysconfdir}/apache2/default-server-ssl.conf
%else
chown -R apache:apache %{_sysconfdir}/httpd/conf.d/vsm-dashboard.conf
%endif

VSM_VERSION=%{version}-%{release}
sed -i "s,%VSM_VERSION%,$VSM_VERSION,g" %{_datadir}/vsm-dashboard/vsm_dashboard/dashboards/vsm/overview/summarys.py

%files
%defattr(-,root,root,-)
%if 0%{?suse_version}
%dir %{_sysconfdir}/apache2
%dir %{_sysconfdir}/apache2/conf.d
%config(noreplace) %attr(-, root, www) %{_sysconfdir}/apache2/conf.d/vsm-dashboard.conf
%config(noreplace) %attr(-, root, www) %{_sysconfdir}/apache2/default-server-ssl.conf
%else
%dir %{_sysconfdir}/httpd/conf.d
%config(noreplace) %attr(-, root, apache) %{_sysconfdir}/httpd/conf.d/vsm-dashboard.conf
%endif

%dir %{_bindir}
%if 0%{?suse_version}
%config(noreplace) %attr(-, root, www) %{_bindir}/lessc
%else
%config(noreplace) %attr(-, root, apache) %{_bindir}/lessc
%endif


%if 0%{?suse_version}
%dir %attr(0755, wwwrun, www) %{_libdir}/less
%else
%dir %attr(0755, apache, apache) %{_libdir}/less
%endif
%{_libdir}/less/*

%if 0%{?suse_version}
%dir %attr(0755, wwwrun, www) %{_datadir}/vsm-dashboard
%else
%dir %attr(0755, apache, apache) %{_datadir}/vsm-dashboard
%endif
%{_datadir}/vsm-dashboard/*


%if 0%{?suse_version}
%config(noreplace) %attr(-, wwwrun, www) %{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py
%else
%config(noreplace) %attr(-, apache, apache) %{_datadir}/vsm-dashboard/vsm_dashboard/local/local_settings.py
%endif
##%%dir %%attr(0755, apache, apache) %%{_datadir}/vsm-dashboard/vsm_dashboard
##%%{_datadir}/vsm-dashboard/vsm_dashboard/*

##%%dir %%attr(0755, apache, apache) %%{_datadir}/vsm-dashboard/static
##%%{_datadir}/vsm-dashboard/static/*
##%%config(noreplace) %%attr(-, root, apache) %%{_datadir}/vsm-dashboard/manage.py

##%%dir %%attr(0755, apache, apache) %%{_sysconfdir}/vsm-dashboard/
##%%config(noreplace) %%attr(-, root, apache) %%{_sysconfdir}/vsm-dashboard/local_settings

##%%{_sysconfdir}/vsm-dashboard/*


