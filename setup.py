#!/usr/bin/env python
# -*- coding: utf-8 -*-


import ast
import re
import sys

from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')


with open('tbd/cli/tbd.py', 'rb') as f:
  version = str(ast.literal_eval(_version_re.search(
    f.read().decode('utf-8')).group(1)))


# Build helper
if sys.argv[-1] == 'tbd-build':
  from sh import pyinstaller
  import shutil
  import tarfile
  import platform

  rel = 'tbd-v{0}-{1}-{2}'.format(
      version, platform.system().lower(), platform.machine())

  print('running pyinstaller...')
  pyinstaller(
      'tbd.spec', clean=True, distpath=rel, _out=sys.stdout, _err=sys.stderr)
  print('success!! tbd binary should be at {0}/tbd'.format(rel))

  print('creating tar.gz file')
  shutil.copy('README.md', rel)
  shutil.copy('LICENSE.md', rel)
  
  with tarfile.open(rel + '.tar.gz', 'w:gz') as tar:
    tar.add(rel)
  print('success!! binary release at {0}'.format(rel + '.tar.gz'))

  sys.exit()


ld = """
tbd is an experimental version control system built on top of Git.
Many people complain that Git is hard to use. We think the problem lies
deeper than the user interface, in the concepts underlying Git. tbd
is an experiment to see what happens if you put a simple veneer on an
app that changes the underlying concepts. Because tbd is implemented
on top of Git (could be considered what Git pros call a \"porcelain\" of
Git), you can always fall back on Git. And of course your coworkers you
share a repo with need never know that you're not a Git aficionado.

More info, downloads and documentation @ `tbd's
website <http://tbd.com>`__.
"""

setup(
    name='tbd',
    version=version,
    description='A version control system built on top of Git',
    long_description=ld,
    author='Santiago Perez De Rosso',
    author_email='sperezde@csail.mit.edu',
    url='http://tbd.com',
    packages=['tbd', 'tbd.cli'],
    install_requires=[
      'pygit2>=0.24.0',
      'clint>=0.3.6',
      'sh>=1.11' if sys.platform != 'win32' else 'pbs>=0.11'
    ],
    license='MIT',
    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Version Control'),
    entry_points={
        'console_scripts': [
            'tbd = tbd.cli.tbd:main'
        ]},
    test_suite='tbd.tests')
