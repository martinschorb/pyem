 # -*- coding: utf-8 -*-

from distutils.core import setup

with open("readme.md", "r") as fh:
    long_description = fh.read()

setup(name='py-EM',
      version='20190820',
      py_modules=['pyEM'],
      description='Tools to interact with Serial EM enabling automated transmission electron microscopy.',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Martin Schorb',
      author_email='schorb@embl.de',
      license='GPLv3',
      install_requires=[
      'numpy',
      'scipy',
      #'re',
      'mrcfile',
      #'time',
      #'operator',      
      ],
      ) 
