import sys

from paver.easy import task, needs, path, sh, cmdopts, options
from paver.setuputils import setup, install_distutils_tasks
from distutils.extension import Extension
from distutils.dep_util import newer

sys.path.insert(0, path('.').abspath())
import version


setup(name='svg_model',
      version=version.getVersion(),
      description='A Python module for parsing an SVG file to a group of '
      'paths.',
      keywords='svg model pymunk',
      author='Christian Fobel',
      author_email='christian@fobel.net',
      url='http://github.com/wheeler-microfluidics/svg_model.git',
      license='LGPLv2.1',
      install_requires=['lxml', 'numpy', 'pandas', 'pint',
                        'pymunk>=4.0.0,<5.0'],
      packages=['svg_model'],
      # Install data listed in `MANIFEST.in`
      include_package_data=True)


@task
@needs('generate_setup', 'minilib', 'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    pass
