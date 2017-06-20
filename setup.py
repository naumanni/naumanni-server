#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from setuptools import find_packages, setup

VERSION_REX = re.compile(r'VERSION\s*=\s*\((.*?)\)')


def get_package_version():
    """returns package version without importing it"""
    base = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(base, 'naumanni/__init__.py')) as fp:
        for line in fp:
            m = VERSION_REX.match(line.strip())
            if not m:
                continue
            return ".".join(m.groups()[0].split(", "))


setup(
    name='naumanni-server',
    version=get_package_version(),
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'aioredis>=0.2.0',
        'click>=6',
        'psutil>=5.2.2',
        'pycurl>=7.43.0',
        'python-dateutil>=2.6.0',
        'tornado>=4.5.1',
        'twitter-text-python>=1.1.0',
        'Werkzeug>=0.12.2',
    ],
    dependency_links=[
    ],
    entry_points={
        'console_scripts': [
            'naumanni=naumanni.cli:cli_entry',
        ],
    },
    extras_require={
        'test': [
            'coverage',
            'flake8',
            'flake8-import-order',
            # 'nnpy',
            'pytest',
            # 'pytest-timeout',
            # 'tcptest',
            'tox',
        ],
        'doc': [
            # 'Sphinx',
            # 'sphinx-rtd-theme',
        ],
        'utils': [
            'boto>=2.47.0',
        ]
    }
)
