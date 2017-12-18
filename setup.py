# -*- coding: utf-8 -*-
#
# Copyright © 2014 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
import os
import sys
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

version = "0.2.1.post1.dev0"

install_requires = [
    'pyramid',
    ]

tests_require = [
    'pytest',
    ]

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []


setup(
    name='pyramid_log',
    version=version,
    description="Include pyramid request attributes in your log messages",
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Logging",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        ],
    keywords="pyramid logging",
    author="Jeff Dairiki",
    author_email="dairiki@dairiki.org",
    url="http://pypi.python.org/pypi/pyramid_log/",
    license="BSD",
    packages=find_packages(),
    # include_package_data=True,
    zip_safe=True,
    setup_requires=pytest_runner,
    install_requires=install_requires,
    tests_require=tests_require,
    )
