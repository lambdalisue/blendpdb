#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from setuptools import setup, find_packages

version = "0.1.0"

def read(filename):
    import os.path
    return open(os.path.join(os.path.dirname(__file__), filename)).read()

setup(
    name="Blend",
    version=version,
    description = "Blending two PDB files to create solvate",
    long_description=read('README.md'),
    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    keywords = "blend, pdb, solvate",
    author = "Alisue",
    author_email = "lambdalisue@hashnote.net",
    url=r"https://github.com/lambdalisue/blend",
    download_url = r"https://github.com/lambdalisue/blend/tarball/master",
    license = 'MIT',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    entry_points = {
        'console_scripts': [
            "blend = blend.blend:main",
        ]
    },
    include_package_data = True,
    zip_safe = True,
    install_requires=[
        'setuptools',
        'PyYAML',
    ],
)
