from setuptools import setup
import os
import re


v = open(os.path.join(os.path.dirname(__file__), 'autodoc_links.py'))
VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(v.read()).group(1)
v.close()

readme = os.path.join(os.path.dirname(__file__), 'README.rst')


setup(name='autodoc_links',
      version=VERSION,
      description="Adds linkable parameters and enhanced superclass info to Sphinx autodoc",
      long_description=open(readme).read(),
      classifiers=[
      'Development Status :: 3 - Alpha',
      'Environment :: Console',
      'Intended Audience :: Developers',
      'Programming Language :: Python',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: Implementation :: CPython',
      'Programming Language :: Python :: Implementation :: PyPy',
      'Topic :: Documentation',
      ],
      keywords='Sphinx',
      author='Mike Bayer',
      author_email='mike@zzzcomputing.com',
      url='http://bitbucket.org/zzzeek/autodoc_links',
      license='MIT',
      py_modules=('autodoc_links',),
      zip_safe=False,
)
