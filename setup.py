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

from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='vinyldns-python',
    version='0.0.1',
    packages=['vinyldns_python'],
    package_dir={'vinyldns_python':'src'},
    url='https://github.com/vinyldns/vinyldns-python',
    license='Apache 2.0',
    author='vinyldns',
    author_email='vinyldns-core@googlegroups.com',
    classifiers=[
        'Topic :: Internet :: Name Service (DNS)',
        'License :: OSI Approved :: Apache Software License',
    ],
    keywords='dns',
    description='Python client library for VinylDNS',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'boto',
        'future',
        'requests'
    ]
)
