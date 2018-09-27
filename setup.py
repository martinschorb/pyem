 # -*- coding: utf-8 -*-

from distutils.core import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='emtools',
      version='20180927',
      py_modules=['emtools'],
      description='Tools to interact with Serial EM enabling automated transmission electron microscopy.',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Martin Schorb',
      author_email='schorb@embl.de',
      license='GPLv3',
      install_requires=[
      'numpy',
      'scipy',
      'tifffile',
      #'re',
      'mrcfile',
      #'time',
      #'operator',      
      ],
      ) 
