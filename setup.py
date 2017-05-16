#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup


install_requires = [
    # 'alembic',
    # 'base58',
    'celery>=4',
    'click>=6',
    'Flask>=0.11',
    # 'Flask-OAuthlib',
    # 'mysql-connector-python-rf',
    # 'nnpy',
    'python-dateutil',
    # 'six',
    # 'sqlalchemy>=1.1.4',
    'tornado',
    # 'websocket-client',
    # 'whisper==0.10.0rc1',
]

setup(
    name='naumanni-server',
    version='0.1',
    packages=find_packages(exclude=['tests']),
    install_requires=install_requires,
    dependency_links=[
        # 'git+https://github.com/nanomsg/nnpy.git#egg=nnpy',
        # 'git+https://github.com/graphite-project/whisper.git@b783ab3f577f3f60db607adda241e29b7242bcf4#egg=whisper-0.10.0rc1',
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
        ]
    }
)
