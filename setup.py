#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys

try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import setup, find_packages


# extract the version number without importing the package
with open('hyperkitty/__init__.py') as fp:
    for line in fp:
        mo = re.match("""VERSION\s*=\s*['"](?P<version>[^'"]+?)['"]""", line)
        if mo:
            __version__ = mo.group('version')
            break
    else:
        print('No version number found')
        sys.exit(1)


# Requirements
REQUIRES = [
    "Django>=1.6",
    "django-gravatar2>=1.0.6",
    "python-social-auth>=0.2.3",
    "djangorestframework>=3.0.0",
    "django-crispy-forms>=1.4.0",
    "rjsmin>=1.0.6",
    "cssmin>=0.2.0",
    "robot-detection>=0.3",
    "pytz>=2012",
    "django-paintstore>=0.1.2",
    "django-compressor>=1.3",
    "django-browserid>=0.11.1",
    "mailmanclient>=1.0.0b1",
    "python-dateutil < 2.0", # python-dateutil 2.0+ is for Python 3
    "networkx>=1.9.1",
    "enum34>=1.0",
    "django-haystack>=2.1.0",
    "django-extensions>=1.3.7",
    "lockfile>=0.9.1",
]
try:
    import django
    if django.VERSION[:2] < (1, 7):
        REQUIRES.append("South>=1.0.0")
except ImportError:
    pass


setup(
    name="HyperKitty",
    version=__version__,
    description="A web interface to access GNU Mailman v3 archives",
    long_description=open('README.rst').read(),
    author='HyperKitty Developers',
    author_email='hyperkitty-devel@lists.fedorahosted.org',
    url="https://gitlab.com/mailman/hyperkitty",
    license="GPLv3",
    classifiers=[
        "Framework :: Django",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Communications :: Email :: Mailing List Servers",
        "Programming Language :: Python :: 2",
        "Programming Language :: JavaScript",
        ],
    keywords='email',
    #packages=find_packages(exclude=["*.test", "test", "*.test.*"]),
    packages=find_packages(),
    include_package_data=True,
    install_requires=REQUIRES,
    tests_require=[
        "mock",
        "Whoosh>=2.5.7",
        "beautifulsoup4>=4.3.2",
        ],
    )
