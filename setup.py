#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from glob import glob
from os.path import basename
from os.path import splitext
from setuptools import find_packages
from setuptools import setup

sys.path.insert(0, path('.').abspath())
import version

# See https://blog.ionelmc.ro/2014/06/25/python-packaging-pitfalls/
setup(name='svg_model',
      version=version.getVersion(),
      description='A Python module for parsing an SVG file to a group of '
      'paths.',
      keywords='svg model pymunk',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='https://github.com/sci-bots/svg-model',
      license='LGPLv2.1',
      install_requires=['lxml', 'pandas>=0.17.0', 'path-helpers', 'pint',
                        'pymunk>=4.0.0,<5.0', 'svgwrite'],
      packages=['svg_model'],
      # Install data listed in `MANIFEST.in`
      include_package_data=True)
