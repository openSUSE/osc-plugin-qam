%define sourcename oscqam
%define name python-oscqam
%define unmangled_version 0.1
%define unmangled_version 0.1
%define release 1
%define OSCPLUGINPATH /var/lib/osc-plugins/
%define OSCQAMPATH %{python_sitelib}/oscqam/

Summary: Plugin for OSC to support the workflow for the QA maintenance department when using the new request / review osc abstractions.
Name: %{name}
Version: 0.1
Release: 0
Source0: %{sourcename}-%{unmangled_version}.tar.gz
License: UNKNOWN
Group: Productivity/Other
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: UNKNOWN <UNKNOWN>
Url: https://wiki.innerweb.novell.com/index.php/RD-OPS_QA/Maintenance/osc-for-qam
BuildRequires: python-devel
BuildRequires: python-setuptools
BuildRequires: osc
Requires: osc

%description
Overview
========

This package provides the plugin for the _osc tool that adds additional
features to support the QA-Maintenance workflow.

The plugin provides the following new features:

- a new subshell that can be started via ``osc qam`` that only accepts the new
  commands of this plugin.

- the following new commands:

  - list [-u user]: list all open reviews for the given user that need review
    by one of the ``qam-*`` groups.

  - assign [-u user] <request_id>: assign the user to do a review for the
    given request_id. This command will attempt to guess the group the user
    would probably like to a review for.

  - unassign [-u user] <request_id>: unassign the user to do a review for the
    given request_id. This command will attempt to guess the group the user
    wants to unassign himself for.

  - approve [-u user] <request_id>: will approve a started review of the user
    for the given request_id.

  - reject [-u user] <request_id>: will reject a started review of the user
    for the given request_id.


Installation
============

Either install the package with your package manager or use the following pip
command:

Development
===========

The oscqam plugin uses pytest_ library to run the test. To setup the project
correctly for usage with it, install it using pip:

.. code:: bash

          cd <src_directory_oscqam>
          pip install --user -e .

Now running the tests with ``py.test`` should work:

.. code:: bash

          cd <src_directory_oscqam>
          py.test ./tests


_osc: https://github.com/openSUSE/osc
_py.test: http://pytest.org/


%prep
%setup -n %{sourcename}-%{unmangled_version} -n %{sourcename}-%{unmangled_version}

%build
python setup.py build


%install
install -d %{buildroot}%{OSCPLUGINPATH}

python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --prefix=%{_prefix}

%py_compile %{buildroot}%{OSCQAMPATH}

ln -s %{OSCQAMPATH}cli.py %{buildroot}%{OSCPLUGINPATH}cli.py

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{OSCQAMPATH}
%{OSCPLUGINPATH}
%{python_sitelib}/%{sourcename}-%{version}-py%{py_ver}.egg-info
