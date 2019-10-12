# Copyright 2018 Comcast Cable Communications Management, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function

import sys
from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test as TestCommand


# Allows one to simply > python3 setup.py test
class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


with open('README.md') as f:
    long_description = f.read()

setup(
    cmdclass={'test': PyTest},
    name='vinyldns-python',
    version='0.9.4',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    url='https://github.com/vinyldns/vinyldns-python',
    license='Apache Software License 2.0',
    author='vinyldns',
    author_email='vinyldns-core@googlegroups.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Internet :: Name Service (DNS)',
        'License :: OSI Approved :: Apache Software License',
    ],
    keywords=[
        'dns', 'python', 'vinyldns',
    ],
    description='Python client library for VinylDNS',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'boto==2.48.0',
        'future==0.17.1',
        'requests==2.20.0',
        'python-dateutil==2.7.5',
    ],
    tests_require=[
        'responses==0.10.4',
        'pytest==3.10.1',
    ],
)
