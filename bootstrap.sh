#!/bin/bash -e
echo "Creating virtualenv..."
virtualenv --clear --python="$(which python3)" ./.virtualenv

echo "Installing dependencies..."
python3 setup.py install
pip install bumpversion
