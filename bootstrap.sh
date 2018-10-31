#!/bin/bash -e

if [ ! -d "./.virtualenv" ]; then
    echo "Creating virtualenv..."
    virtualenv --clear --python="$(which python3)" ./.virtualenv
fi

if ! diff ./requirements.txt ./.virtualenv/requirements.txt &> /dev/null; then
     echo "Installing dependencies..."
     .virtualenv/bin/python ./.virtualenv/bin/pip install -r ./requirements.txt
     cp ./requirements.txt ./.virtualenv/
fi
