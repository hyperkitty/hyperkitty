#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
    name="HyperKitty",
    version="0.1",
    description="A web interface to access GNU Mailman v3 archives",
    long_description=open('README.rst').read(),
    url="https://fedorahosted.org/hyperkitty/",
    packages=find_packages(exclude=["*.test", "test", "*.test.*"]),
    include_package_data=True,
    install_requires=open('requirements.txt').read(),
    )
