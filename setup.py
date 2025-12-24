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

from glob import glob
from os.path import basename, splitext

from setuptools import find_packages, setup


with open("README.md", encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="vinyldns-python",
    version="0.9.7",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    url="https://github.com/vinyldns/vinyldns-python",
    license="Apache Software License 2.0",
    author="vinyldns",
    author_email="vinyldns-core@googlegroups.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Internet :: Name Service (DNS)",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
    ],
    keywords=["dns", "python", "vinyldns"],
    description="Python client library for VinylDNS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "boto3>=1.26.0",
        "requests>=2.20.0",
        "python-dateutil>=2.7.5",
    ],
    tests_require=[
        "responses==0.10.4",
        "pytest==3.10.1",
    ],
)
