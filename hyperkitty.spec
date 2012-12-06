%global pypi_name HyperKitty

Name:           hyperkitty
Version:        0.1.3
Release:        1%{?dist}
Summary:        A web interface to access GNU Mailman v3 archives

License:        GPLv3
URL:            https://fedorahosted.org/hyperkitty/
Source0:        http://pypi.python.org/packages/source/H/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch
 
BuildRequires:  python-devel
BuildRequires:  python-sphinx
# Unit tests in %%check
BuildRequires:  Django
BuildRequires:  kittystore
BuildRequires:  django-rest-framework >= 0.3.3
BuildRequires:  django-social-auth >= 0.7.0

Requires:       Django >= 1.4
Requires:       django-gravatar2
Requires:       django-social-auth >= 0.7.0
Requires:       django-rest-framework >= 0.3.3
Requires:       mailman >= 3.0.0b2
Requires:       kittystore


%description
HyperKitty is an open source Django application under development. It aims at providing a web interface to access GNU Mailman archives.
The code is available from: http://bzr.fedorahosted.org/bzr/hyperkitty/.
The documentation can be browsed online at https://hyperkitty.readthedocs.org/.

%prep
%setup -q -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

# generate html docs 
sphinx-build doc html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

%build
%{__python} setup.py build


%install
%{__python} setup.py install --skip-build --root %{buildroot}


%check
%{__python} %{_bindir}/django-admin test --pythonpath=`pwd` --settings=hyperkitty.tests_conf.settings_tests hyperkitty


%files
%doc html README.rst COPYING.txt
%{python_sitelib}/%{name}
%{python_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info


%changelog
* Thu Nov 29 2012 Aurelien Bompard - 0.1.3-1
- Initial package.
