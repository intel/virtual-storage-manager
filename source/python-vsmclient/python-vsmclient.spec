%define version %{getenv:VERSION}
%define release %{getenv:RELEASE}

Name:             python-vsmclient
%if 0%{?suse_version}
Version:          2.0.0
Release:          217
%else
Version:          %{version}
Release:          %{release}
%endif
Summary:          Python API and CLI for VSM

Group:            Development/Languages
License:          Apache License 2.0
URL:              http://github.com/01org/virtual-storage-manager
Source:           %{name}-%{version}.tar.gz

#
# patches_base=1.0.1
#
BuildArch:        noarch
BuildRequires:    python-setuptools
BuildRequires:    python-argparse
BuildRequires:    python-prettytable
BuildRequires:    python-requests
BuildRequires:    python-simplejson
%if 0%{?suse_version}
BuildRequires:    fdupes
%else
Requires:         python-httplib2
%endif
Requires:         python-prettytable
Requires:         python-setuptools

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

%if 0%{?suse_version}
%fdupes %{buildroot}
%endif

%files
%doc LICENSE
%{_bindir}/vsm
%{python_sitelib}/vsmclient
%{python_sitelib}/*.egg-info
