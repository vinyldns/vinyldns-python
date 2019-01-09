#!/usr/bin/env bash

DIR=$( cd $(dirname $0) ; pwd -P )

function usage {
    printf "usage: release.sh [OPTIONS]\n\n"
    printf "Bumps the version and releases the package to pypi\n\n"
    printf "options:\n"
    printf "\t-b, --bump: which segment to bump: major | minor | patch\n"
    printf "\t-g, --git: push after release to git (default is off)\n"
    printf "\t-p, --production: use real pypi instead of test pypi (test is default)\n"
    printf "\t-k, --key-id: the key id to use to sign the artifacts\n"
}

RELEASE_URL="https://test.pypi.org/legacy/"
KEY_ID=
GIT_PUSH="false"
KEY_ID=
VERSION_SEGMENT="patch"

while [ "$1" != "" ]; do
    case "$1" in
        -g | --git )
            GIT_PUSH="true"
            shift
            ;;
        -p | --production )
            RELEASE_URL="https://pypi.org/legacy/"
            shift
            ;;
        -k | --key-id )
            KEY_ID="$2"
            shift
            ;;
        -b | --bump )
            VERSION_SEGMENT="$2"
            shift
            ;;
        --)              # End of all options.
            shift
            break
            ;;
        -?*)
            printf 'WARN: Unknown option (ignored): %s\n' "$1" >&2
            shift
            ;;
        *)               # Default case: If no more options then break out of the loop.
            break
    esac
    shift
done

if [ -z "$KEY_ID" ]; then
    echo "You must specify a GPG KEY ID on your system to use to sign the artifacts"
    usage
    exit 1
fi

echo "Clearing the dist directory..."
rm -rf ${DIR}/dist

bump_result=0
if [ "${VERSION_SEGMENT}" == "major" ]; then
    echo "Bumping the major version..."
    bump_result=$(bumpversion major)
elif [ "${VERSION_SEGMENT}" == "minor" ]; then
    echo "Bumping the minor version..."
    bump_result=$(bumpversion minor)
else
    echo "Bumping the patch version..."
    bump_result=$(bumpversion patch)
fi

if [ "${bump_result}" != 0 ]; then
    echo "Bumping version failed ${bump_result}!"
    exit 1
fi

echo "Building the artifacts..."
python3 setup.py sdist bdist_wheel

echo "Signing the artifacts..."
cd ${DIR}/dist
for file in $(ls);
do
    echo "gpg -a -u ${KEY_ID} --detach-sign $file"
    gpg -a -u ${KEY_ID} --detach-sign $file
done

echo "Uploading to pypi at ${RELEASE_URL}..."
twine upload --repository-url ${RELEASE_URL} ${DIR}/dist/*

if [[ "$GIT_PUSH" == "true" ]]; then
    echo "Pushing git tags..."
    git push
    git push --tags
else
    echo "Skipping push to git!"
fi
