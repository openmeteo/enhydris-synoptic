#!/usr/bin/env python

from setuptools import setup, find_packages


installation_requirements = [
    "enhydris>=0.5,<0.7",
    "pandas>=0.14",
    "matplotlib>=1.4",
]

packages = find_packages(exclude=['*.tests', '*.tests.*', 'tests.*', 'tests',
                                  ])

kwargs = {
    'name': "enhydris-synoptic",
    'version': __import__('enhydris_synoptic').__version__,
    'license': "AGPL3",
    'description': "View current weather conditions in Enhydris",
    'author': "Antonis Christofides",
    'author_email': "anthony@itia.ntua.gr",
    'packages': packages,
    'install_requires': installation_requirements,
    'test_suite': 'runtests.runtests',
    'tests_require': ['model-mommy>=1.2.4'],
}

setup(**kwargs)
