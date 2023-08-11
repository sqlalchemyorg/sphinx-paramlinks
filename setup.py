import os
import re

from setuptools import setup


v = open(
    os.path.join(os.path.dirname(__file__), "sphinx_paramlinks/__init__.py")
)
VERSION = (
    re.compile(r".*__version__ = [\"'](.*?)[\"']", re.S)
    .match(v.read())
    .group(1)
)
v.close()

readme = os.path.join(os.path.dirname(__file__), "README.rst")


setup(
    name="sphinx-paramlinks",
    version=VERSION,
    description="Allows param links in Sphinx function/method "
    "descriptions to be linkable",
    long_description=open(readme).read(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Framework :: Sphinx :: Extension",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Documentation",
    ],
    keywords="sphinx",
    author="Mike Bayer",
    author_email="mike@zzzcomputing.com",
    url="http://github.com/sqlalchemyorg/sphinx-paramlinks",
    license="MIT",
    packages=["sphinx_paramlinks"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Sphinx>=4.0.0",
        "docutils",
    ],
)
