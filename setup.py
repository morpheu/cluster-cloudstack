# -*- coding: utf-8 -*-

import codecs

from setuptools import setup, find_packages

from cluster_cloudstack import __version__

README = codecs.open('README.md', encoding='utf-8').read()

test_requires = [
    "mock==1.0.1",
    "flake8==2.1.0",
    "coverage==3.7.1"
]

setup(
    name="cluster-cloudstack",
    version=__version__,
    description="Cloudstack cluster management tools",
    long_description=README,
    url="https://github.com/morpheu/cluster-cloudstack",
    author="Paulo Sousa",
    author_email="paulo.sousa@corp.globo.com",
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Clustering"
    ],
    packages=find_packages(exclude=["docs", "tests"]),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'cluster-cloudstack = cluster_cloudstack.control:main'
        ]
    },
    extras_require={
        'tests': test_requires
    }
)
