SHELL=bash

# Check that the required version of make is being used
REQ_MAKE_VER:=3.82
ifneq ($(REQ_MAKE_VER),$(firstword $(sort $(MAKE_VERSION) $(REQ_MAKE_VER))))
   $(error The version of MAKE $(REQ_MAKE_VER) or higher is required; you are running $(MAKE_VERSION))
endif

.ONESHELL:

.PHONY: install
install:
	@set -euo pipefail
	echo "Updating pip"
	python -m pip install --upgrade pip
	echo "Installing dependencies"
	pip install virtualenv
	chmod +x bootstrap.sh
	bash bootstrap.sh

.PHONY: test
test:
	@set -euo pipefail
	echo "Running unit and functional tests"
	tox -e check,py39,func_test

.PHONY: build
build:
	@set -euo pipefail
	echo "Clearing the dist directory..."
	rm -rf dist
	python setup.py sdist bdist_wheel