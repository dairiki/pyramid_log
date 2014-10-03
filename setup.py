# -*- coding: utf-8 -*-
#
# Copyright © 2014 Geoffrey T. Dairiki <dairiki@dairiki.org>
#
import sys, os
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

version = "0.1"

install_requires = [
    'pyramid',
    'zope.proxy',
    ]

tests_require = [
    'pytest',
    ]


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ['pyramid_log/tests.py']

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='pyramid_log',
    version=version,
    description="Include pyramid request attributes in your log messages",
    long_description=README + '\n\n' + CHANGES,
     classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Framework :: Pyramid",
        "Topic :: System :: Logging",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        ],
    keywords="pyramid logging",
    author="Jeff Dairiki",
    author_email="dairiki@dairiki.org",
    url="http://pypi.python.org/pypi/pyramid_log/",
    license="BSD",
    packages=find_packages(),
    #include_package_data=True,
    zip_safe=True,
    install_requires=install_requires,
    tests_require=tests_require,
    cmdclass = {'test': PyTest},
    )
