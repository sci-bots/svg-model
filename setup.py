import sys
from distutils.core import setup

sys.path.insert(0, '.')
import version


setup(name='svg_model',
      version=version.getVersion(),
      description='A Python module for parsing an SVG file to a group of '
      'paths.',
      keywords='svg model pymunk',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='http://github.com/wheeler-microfluidics/svg_model.git',
      license='GPL',
      install_requires=['numpy', 'pandas', 'pint', 'pymunk>=4.0.0'],
      packages=['svg_model'],
      # Install data listed in `MANIFEST.in`
      include_package_data=True)
