#!/bin/bash -e

if [ ! -d "./.virtualenv" ]; then
    echo "Creating virtualenv..."
    virtualenv --clear --python="$(which python3)" ./.virtualenv
fi

 echo "Installing dependencies..."
 python3 setup.py install
