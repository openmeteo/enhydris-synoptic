#!/usr/bin/env python

from setuptools import setup, find_packages


installation_requirements = [
    "enhydris>=0.5,<0.6",
]

packages = find_packages(exclude=['*.tests', '*.tests.*', 'tests.*', 'tests',
                                  ])

kwargs = {
    'name': "enhydris-synoptic",
    'version': __import__('enhydris_synopic').__version__,
    'license': "AGPL3",
    'description': "View current weather conditions in Enhydris",
    'author': "Antonis Christofides",
    'author_email': "anthony@itia.ntua.gr",
    'packages': packages,
    'install_requires': installation_requirements,
    'test_suite': 'runtests.runtests',
}

setup(**kwargs)
