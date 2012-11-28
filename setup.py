#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

setup(
    name="HyperKitty",
    version="0.1.3",
    description="A web interface to access GNU Mailman v3 archives",
    long_description=open('README.rst').read(),
    author='HyperKitty Developers',
    author_email='hyperkitty-devel@lists.fedorahosted.org',
    url="https://fedorahosted.org/hyperkitty/",
    license="GPLv3",
    classifiers=[
        "Framework :: Django",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Communications :: Email :: Mailing List Servers",
        "Programming Language :: Python :: 2",
        "Programming Language :: JavaScript",
        ],
    keywords='email',
    #packages=find_packages(exclude=["*.test", "test", "*.test.*"]),
    packages=find_packages(),
    include_package_data=True,
    install_requires=open('requirements.txt').read(),
    )
