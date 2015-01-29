Name:             python-vsmclient
Version:          2015.01
Release:          1.0%{?dist}
Summary:          Python API and CLI for  vsm

Group:            Development/Languages
License:          Intel Reserved
URL:              http://intel.com/itflex
Source0:          %{name}-%{version}.tar.gz

#
# patches_base=1.0.1
#
BuildArch:        noarch
BuildRequires:    python-setuptools
BuildRequires:    python-argparse
BuildRequires:    python-prettytable
BuildRequires:    python-requests
BuildRequires:    python-simplejson
Requires:         python-httplib2
Requires:         python-prettytable
Requires:         python-setuptools
Requires:         python-argparse

%description
This is a client for the  vsm API. There's a Python API (the
vsmclient module), and a command-line script (vsm). Each implements
100% of the  vsm API.

%prep
%setup -q
sed -i '/setup_requires/d; /install_requires/d; /dependency_links/d' setup.py
rm -rf python_vsmclient.egg-info

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root %{buildroot}

# Delete tests
rm -fr %{buildroot}%{python_sitelib}/tests

%files
%doc LICENSE
%{_bindir}/vsm
%{python_sitelib}/vsmclient
%{python_sitelib}/*.egg-info

%changelog
* Mon Feb 17 2014 Ji You <ji.you@intel.com> - 2014.2.17-2
- Initial release
