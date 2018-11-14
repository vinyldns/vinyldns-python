========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|



.. |travis| image:: https://travis-ci.org/vinyldns/vinyldns-python.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/vinyldns/vinyldns-python

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/vinyldns/vinyldns-python?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/vinyldns/vinyldns-python

.. |requires| image:: https://requires.io/github/vinyldns/vinyldns-python/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/vinyldns/vinyldns-python/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/vinyldns/vinyldns-python/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/vinyldns/vinyldns-python

.. |version| image:: https://img.shields.io/pypi/v/vinyldns.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/vinyldns

.. |commits-since| image:: https://img.shields.io/github/commits-since/vinyldns/vinyldns-python/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/vinyldns/vinyldns-python/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/vinyldns.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/vinyldns

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/vinyldns.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/vinyldns

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/vinyldns.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/vinyldns


.. end-badges

Python client library for VinylDNS

* Free software: Apache Software License 2.0

Installation
============

::

    pip install vinyldns

Documentation
=============


To use the project:

.. code-block:: python

    import vinyldns
    vinyldns.longest()


Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
