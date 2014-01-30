%global pypi_name HyperKitty
#%%global prerel 1

Name:           hyperkitty
Version:        0.1.7
Release:        %{?prerel:0.}1%{?dist}
Summary:        A web interface to access GNU Mailman v3 archives

License:        GPLv3
URL:            https://fedorahosted.org/hyperkitty/
Source0:        http://pypi.python.org/packages/source/H/%{pypi_name}/%{pypi_name}-%{version}%{?prerel:dev}.tar.gz

# To get SOURCE1:
#   git clone https://github.com/hyperkitty/hyperkitty_standalone.git
#   make sdist -C hyperkitty_standalone
#   mv hyperkitty_standalone/dist/hyperkitty_standalone-%{version}.tar.gz .
Source1:        hyperkitty_standalone-%{version}%{?prerel:dev}.tar.gz


BuildArch:      noarch

BuildRequires:  python-devel
BuildRequires:  python-sphinx
# Unit tests in %%check
BuildRequires:  kittystore
BuildRequires:  django-gravatar2
BuildRequires:  django-rest-framework >= 2.2.0
BuildRequires:  django-social-auth >= 0.7.1
BuildRequires:  django-crispy-forms
BuildRequires:  django-assets
BuildRequires:  python-rjsmin
BuildRequires:  python-cssmin
BuildRequires:  python-mailman-client
BuildRequires:  python-robot-detection
BuildRequires:  pytz
BuildRequires:  django-paintstore
%if 0%{fedora} && 0%{fedora} < 18
BuildRequires:  Django
BuildRequires:  Django-south
%else
BuildRequires:  python-django
BuildRequires:  python-django-south
%endif

# SELinux
BuildRequires:  checkpolicy, selinux-policy-devel, /usr/share/selinux/devel/policyhelp
BuildRequires:  hardlink

Requires:       django-gravatar2
Requires:       django-social-auth >= 0.7.1
Requires:       django-rest-framework >= 2.2.0
#Requires:       mailman >= 3:3.0.0
Requires:       mailman3
Requires:       kittystore
Requires:       django-crispy-forms
Requires:       django-assets
Requires:       python-rjsmin
Requires:       python-cssmin
Requires:       python-mailman-client
Requires:       python-robot-detection
Requires:       pytz
Requires:       django-paintstore
%if 0%{fedora} && 0%{fedora} < 18
Requires:       Django >= 1.4
Requires:       Django-south
%else
Requires:       python-django >= 1.4
Requires:       python-django-south
%endif


%description
HyperKitty is an open source Django application under development. It aims at
providing a web interface to access GNU Mailman archives.
The code is available from: https://github.com/hyperkitty/hyperkitty .
The documentation can be browsed online at https://hyperkitty.readthedocs.org .


%package selinux
%global selinux_variants mls targeted
Summary:        SELinux policy module for %{name}
Requires:       %{name} = %{version}-%{release}
%{!?_selinux_policy_version: %global _selinux_policy_version %(sed -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp 2>/dev/null)}
%if "%{_selinux_policy_version}" != ""
Requires:      selinux-policy >= %{_selinux_policy_version}
%endif

Requires(post):   /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles, %{name}
Requires(postun): /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles, %{name}

%description selinux
This is the SELinux module for %{name}, install it if you are using SELinux.



%prep
%setup -q -n %{pypi_name}-%{version}%{?prerel:dev} -a 1
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
mv hyperkitty_standalone-%{version}%{?prerel:dev} hyperkitty_standalone
# remove shebang on manage.py
sed -i -e '1d' hyperkitty_standalone/manage.py
# remove executable permissions on wsgi.py
chmod -x hyperkitty_standalone/wsgi.py
# remove __init__.py in hyperkitty_standalone to prevent it from being
# installed (find_package won't find it). It's empty anyway.
rm -f hyperkitty_standalone/__init__.py

# SELinux
mkdir SELinux
echo '%{_localstatedir}/lib/%{name}/sites(/.*)? gen_context(system_u:object_r:httpd_sys_content_t,s0)' \
    > SELinux/%{name}.fc
# remember to bump the following version if the policy is updated
echo "policy_module(%{name}, 1.0)" > SELinux/%{name}.te


%build
%{__python} setup.py build

# generate html docs
sphinx-build doc html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

# SELinux
cd SELinux
for selinuxvariant in %{selinux_variants}; do
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
  mv %{name}.pp %{name}.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -


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
sed -e 's,/path/to/hyperkitty_standalone/static,%{_localstatedir}/lib/%{name}/sites/default/static,g' \
    -e 's,/path/to/hyperkitty_standalone,%{_sysconfdir}/%{name}/sites/default,g' \
     hyperkitty_standalone/hyperkitty.apache.conf \
     > %{buildroot}/%{_sysconfdir}/httpd/conf.d/hyperkitty.conf
touch --reference hyperkitty_standalone/hyperkitty.apache.conf \
    %{buildroot}/%{_sysconfdir}/httpd/conf.d/hyperkitty.conf
# SQLite databases directory and static files
mkdir -p %{buildroot}%{_localstatedir}/lib/%{name}/sites/default/static
mkdir -p %{buildroot}%{_localstatedir}/lib/%{name}/sites/default/db
sed -i -e 's,/path/to/rw,%{_localstatedir}/lib/%{name}/sites/default/db,g' \
       -e 's,^STATIC_ROOT = .*$,STATIC_ROOT = "%{_localstatedir}/lib/%{name}/sites/default/static/",g' \
    %{buildroot}%{_sysconfdir}/%{name}/sites/default/settings.py
touch --reference hyperkitty_standalone/settings.py \
    %{buildroot}%{_sysconfdir}/%{name}/sites/default/settings.py

# SELinux
for selinuxvariant in %{selinux_variants}; do
  install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
  install -p -m 644 SELinux/%{name}.pp.${selinuxvariant} \
    %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{name}.pp
done
/usr/sbin/hardlink -cv %{buildroot}%{_datadir}/selinux



%check
touch hyperkitty_standalone/__init__.py
%{__python} hyperkitty_standalone/manage.py test --pythonpath=`pwd` hyperkitty
rm -f hyperkitty_standalone/__init__.py


%post
# Build the static files cache
%{__python} %{_sysconfdir}/%{name}/sites/default/manage.py \
    collectstatic --noinput >/dev/null || :
%{__python} %{_sysconfdir}/%{name}/sites/default/manage.py \
    assets build --parse-templates &>/dev/null || :


%post selinux
for selinuxvariant in %{selinux_variants}; do
  /usr/sbin/semodule -s ${selinuxvariant} -i \
    %{_datadir}/selinux/${selinuxvariant}/%{name}.pp &> /dev/null || :
done
/sbin/fixfiles -R %{name} restore || :
/sbin/restorecon -R %{_localstatedir}/lib/%{name} || :

%postun selinux
if [ $1 -eq 0 ] ; then
  for selinuxvariant in %{selinux_variants}; do
    /usr/sbin/semodule -s ${selinuxvariant} -r %{name} &> /dev/null || :
  done
  /sbin/fixfiles -R %{name} restore || :
  [ -d %{_localstatedir}/lib/%{name} ]  && \
    /sbin/restorecon -R %{_localstatedir}/lib/%{name} &> /dev/null || :
fi


%files
%doc html README.rst COPYING.txt
%config(noreplace) %{_sysconfdir}/%{name}
%config(noreplace) %attr(640,root,apache) %{_sysconfdir}/%{name}/sites/default/settings.py
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%{python_sitelib}/%{name}
%{python_sitelib}/%{pypi_name}-%{version}%{?prerel:dev}-py?.?.egg-info
%dir %{_localstatedir}/lib/%{name}
%dir %{_localstatedir}/lib/%{name}/sites
%dir %{_localstatedir}/lib/%{name}/sites/default
%dir %{_localstatedir}/lib/%{name}/sites/default/static
%attr(755,apache,apache) %{_localstatedir}/lib/%{name}/sites/default/db

%files selinux
%defattr(-,root,root,0755)
%doc SELinux/*
%{_datadir}/selinux/*/%{name}.pp


%changelog
* Mon Nov 25 2013 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.7-0.1
- add SELinux policy module, according to:
  http://fedoraproject.org/wiki/SELinux_Policy_Modules_Packaging_Draft

* Thu Aug 15 2013 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.7-0.1
- don't remove the static files cache on uninstall (it may have local
  modifications)

* Tue Jul 23 2013 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.6-1
- version 0.1.6

* Thu Mar 28 2013 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.5-0.2
- put collected static files in _localstatedir

* Tue Feb 19 2013 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.4-1
- update to 0.1.4

* Thu Nov 29 2012 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.3-1
- Initial package.
