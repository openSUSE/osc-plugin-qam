#
# spec file for package python-oscqam
#
# Copyright (c) 2015 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.


Name:           python-oscqam
Version:        0.3.0
Release:        0
Summary:        Plugin for OSC to support the workflow of the QA maintenance department
License:        SUSE-NonFree
Group:          Productivity/Other
Url:            http://qam.suse.de
Source0:        %{name}-%{version}.tar.gz
BuildRequires: python-devel
BuildRequires: python-setuptools
BuildRequires: osc
Requires: osc >= 0.148.0
Requires: python-PrettyTable
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
%py_requires
%if 0%{?suse_version} && 0%{?suse_version} <= 1110
%{!?python_sitelib: %define python_sitelib %(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%else
BuildArch:      noarch
%endif
%define OSCPLUGINPATH /usr/lib/osc-plugins/
%define OSCQAMPATH %{python_sitelib}/oscqam/

%description
Plugin for OSC to support the workflow of the QA maintenance department for SLE 12.

%prep
%setup -q

%build
python setup.py build

%install
install -d %{buildroot}%{OSCPLUGINPATH}

python setup.py install --prefix=%{_prefix} --root=%{buildroot}

%py_compile %{buildroot}%{OSCQAMPATH}

ln -s %{OSCQAMPATH}cli.py %{buildroot}%{OSCPLUGINPATH}cli.py
%py_compile %{buildroot}%{OSCPLUGINPATH}

%files
%defattr(-,root,root,-)
%doc README.rst
%{OSCQAMPATH}
%{OSCPLUGINPATH}
%{python_sitelib}/python_oscqam-%{version}-py%{py_ver}.egg-info

%changelog
