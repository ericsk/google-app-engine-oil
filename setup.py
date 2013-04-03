#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    print 'please install setuptools first'

from pkg_resources import DistributionNotFound

import sys
import os
import glob

execfile(os.path.join('bin', 'release.py'))

# setup params

required_modules = []
extra_modules = {}

setup(
    name='gaeo',
    version=version,
    author=author,
    author_email=email,
    download_url=download_url,
    license=license,
    keywords='appengine, webframework',
    description=description,
    long_description=long_description,
    url=url,
    zip_safe=False,
    install_requires=required_modules,
    extras_require=extra_modules,
    include_package_data=True,
    packages=find_packages(),
    entry_points="""
    [console_scripts]
    gaeo = bin.gaeo:commandline
    gaeogen = bin.gaeogen:commandline
    """,
    classifiers=['Development Status :: 3 - Alpha',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'Programming Language :: Python'],
    )

