from distutils.core import setup

import version


setup(name='svg_model',
      version=version.getVersion(),
      description='A Python module for parsing an SVG file to a group of '
      'paths.',
      keywords='svg model pymunk',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='http://github.com/cfobel/svg_model.git',
      license='GPL',
      packages=['svg_model', 'svg_model.svgload'])
