%global pypi_name HyperKitty

Name:           hyperkitty
Version:        0.1.3
Release:        3%{?dist}
Summary:        A web interface to access GNU Mailman v3 archives

License:        GPLv3
URL:            https://fedorahosted.org/hyperkitty/
Source0:        http://pypi.python.org/packages/source/H/%{pypi_name}/%{pypi_name}-%{version}.tar.gz
# bzr branch bzr://bzr.fedorahosted.org/bzr/hyperkitty/hyperkitty_standalone
Source1:        hyperkitty_standalone.tar.gz
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
HyperKitty is an open source Django application under development. It aims at
providing a web interface to access GNU Mailman archives.
The code is available from: http://bzr.fedorahosted.org/bzr/hyperkitty/.
The documentation can be browsed online at https://hyperkitty.readthedocs.org/.

%prep
%setup -q -n %{pypi_name}-%{version} -a 1
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
# remove shebang on manage.py
sed -i -e '1d' hyperkitty_standalone/manage.py
# remove executable permissions on wsgi.py
chmod -x hyperkitty_standalone/wsgi.py
# remove __init__.py in hyperkitty_standalone to prevent it from being
# installed (find_package won't find it). It's empty anyway.
rm -f hyperkitty_standalone/__init__.py


%build
%{__python} setup.py build

# generate html docs
sphinx-build doc html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}


%install
%{__python} setup.py install --skip-build --root %{buildroot}

# Install the Django files
mkdir -p %{buildroot}%{_sysconfdir}/%{name}/sites/default
cp -p hyperkitty_standalone/{manage,settings,urls,wsgi}.py \
    %{buildroot}%{_sysconfdir}/%{name}/sites/default/
touch --reference hyperkitty_standalone/manage.py \
    %{buildroot}%{_sysconfdir}/%{name}/sites/default/__init__.py
# Mailman config file
sed -e 's,/path/to/hyperkitty_standalone,%{_sysconfdir}/%{name}/sites/default,g' \
    hyperkitty_standalone/hyperkitty.cfg \
    > %{buildroot}%{_sysconfdir}/%{name}/sites/default/hyperkitty.cfg
touch --reference hyperkitty_standalone/hyperkitty.cfg \
    %{buildroot}%{_sysconfdir}/%{name}/sites/default/hyperkitty.cfg
# Apache HTTPd config file
mkdir -p %{buildroot}/%{_sysconfdir}/httpd/conf.d/
sed -e 's,/path/to/hyperkitty_standalone,%{_sysconfdir}/%{name}/sites/default,g' \
     hyperkitty_standalone/hyperkitty.apache.conf \
     > %{buildroot}/%{_sysconfdir}/httpd/conf.d/hyperkitty.conf
touch --reference hyperkitty_standalone/hyperkitty.apache.conf \
    %{buildroot}/%{_sysconfdir}/httpd/conf.d/hyperkitty.conf
# SQLite databases directory
mkdir -p %{buildroot}%{_localstatedir}/lib/%{name}/sites/default
sed -i -e 's,/path/to/rw,%{_localstatedir}/lib/%{name}/sites/default,g' \
    %{buildroot}%{_sysconfdir}/%{name}/sites/default/settings.py
touch --reference hyperkitty_standalone/settings.py \
    %{buildroot}%{_sysconfdir}/%{name}/sites/default/settings.py


%check
%{__python} %{_bindir}/django-admin test --pythonpath=`pwd` \
    --settings=hyperkitty.tests_conf.settings_tests hyperkitty


%post
# Build the static files cache
%{__python} %{_sysconfdir}/%{name}/sites/default/manage.py \
    collectstatic --noinput >/dev/null || :


%preun
# The static files are a cache and can be removed with the package
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    rm -rf %{_sysconfdir}/%{name}/sites/default/static
fi


%files
%doc html README.rst COPYING.txt
%config(noreplace) %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/httpd/conf.d/hyperkitty.conf
%{python_sitelib}/%{name}
%{python_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info
%dir %{_localstatedir}/lib/%{name}
%dir %{_localstatedir}/lib/%{name}/sites
%attr(755,apache,apache) %{_localstatedir}/lib/%{name}/sites/default


%changelog
* Thu Nov 29 2012 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.3-1
- Initial package.
