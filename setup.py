#!/usr/bin/env python3

from setuptools import setup, find_packages


installation_requirements = [
    "enhydris>=1.1,<2",
    "pandas>=0.14",
    "matplotlib>=1.4,<2",
    "celery>=3.1,<4",
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
    'url': "https://github.com/openmeteo/enhydris-synoptic",
    'packages': packages,
    'package_data': {'enhydris_synoptic': ['templates/*']},
    'install_requires': installation_requirements,
    'test_suite': 'runtests.runtests',
    'tests_require': ['model-mommy>=1.2.4'],
    'classifiers': [
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: "
            "GNU Affero General Public License v3 or later (AGPLv3+)",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
    ],
}

setup(**kwargs)
