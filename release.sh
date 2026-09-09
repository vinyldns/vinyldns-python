#!/usr/bin/env bash

# Enable strict error handling before anything else
set -euo pipefail

DIR=$( cd $(dirname $0) ; pwd -P )

function usage {
    printf "usage: release.sh [OPTIONS]\n\n"
    printf "Bumps the version and releases the package to pypi\n\n"
    printf "options:\n"
    printf "\t-b, --bump: which segment to bump: major | minor | patch\n"
    printf "\t-p, --production: use real pypi instead of test pypi (test is default)\n"
    printf "\t-k, --key-id: the key id to use to sign the artifacts\n"
    printf "\t-r, --remote: the git remote name to push to (required for production)\n"
}

function check_command {
    if ! command -v "$1" &> /dev/null; then
        echo "ERROR: Required command '$1' is not available" >&2
        exit 1
    fi
}

function check_python_module {
    if ! python3 -c "import $1" &> /dev/null; then
        echo "ERROR: Required Python module '$1' is not installed" >&2
        echo "Install it with: pip install $1" >&2
        exit 1
    fi
}

function check_git_clean {
    if [ -n "$(git status --porcelain)" ]; then
        echo "ERROR: Working directory is not clean. Commit or stash changes before releasing." >&2
        git status --short >&2
        exit 1
    fi
}

function check_gpg_key {
    local key_id="$1"
    if ! gpg --list-secret-keys "$key_id" &> /dev/null; then
        echo "ERROR: GPG key '$key_id' not found in local keyring" >&2
        echo "Available keys:" >&2
        gpg --list-secret-keys --keyid-format LONG >&2
        exit 1
    fi
}

RELEASE_URL="--repository-url https://test.pypi.org/legacy/"
KEY_ID=
VERSION_SEGMENT="patch"
RELEASE_REMOTE=

while [ $# -gt 0 ]; do
    case "$1" in
        -p | --production )
            RELEASE_URL=""
            shift
            ;;
        -k | --key-id )
            if [ $# -lt 2 ]; then
                echo "ERROR: --key-id requires a value" >&2
                usage
                exit 1
            fi
            KEY_ID="$2"
            shift 2
            ;;
        -b | --bump )
            if [ $# -lt 2 ]; then
                echo "ERROR: --bump requires a value" >&2
                usage
                exit 1
            fi
            VERSION_SEGMENT="$2"
            shift 2
            ;;
        -r | --remote )
            if [ $# -lt 2 ]; then
                echo "ERROR: --remote requires a value" >&2
                usage
                exit 1
            fi
            RELEASE_REMOTE="$2"
            shift 2
            ;;
        --)              # End of all options.
            shift
            break
            ;;
        -?*)
            echo "ERROR: Unknown option: $1" >&2
            usage
            exit 1
            ;;
        *)               # Default case: If no more options then break out of the loop.
            break
    esac
done

if [ -z "$KEY_ID" ]; then
    echo "ERROR: You must specify a GPG KEY ID to use for signing artifacts" >&2
    usage
    exit 1
fi

# Check that remote is specified for production releases
if [ -z "${RELEASE_URL}" ] && [ -z "$RELEASE_REMOTE" ]; then
    echo "ERROR: You must specify a remote name with --remote for production releases" >&2
    usage
    exit 1
fi

# Validate version segment
if [[ ! "$VERSION_SEGMENT" =~ ^(major|minor|patch)$ ]]; then
    echo "ERROR: Invalid version segment '$VERSION_SEGMENT'. Must be major, minor, or patch." >&2
    exit 1
fi

echo "=== Running preflight checks ==="

# Check that required commands are available
echo "Checking required commands..."
check_command git
check_command python3
check_command gpg
check_command bumpversion

# Check Python version (requires 3.11+ per setup.py)
echo "Checking Python version..."
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_MAJOR=3
REQUIRED_MINOR=11
CURRENT_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
CURRENT_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$CURRENT_MAJOR" -lt "$REQUIRED_MAJOR" ] || \
   ([ "$CURRENT_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$CURRENT_MINOR" -lt "$REQUIRED_MINOR" ]); then
    echo "ERROR: Python $REQUIRED_MAJOR.$REQUIRED_MINOR+ required, but found $PYTHON_VERSION" >&2
    exit 1
fi
echo "✓ Python $PYTHON_VERSION"

# Check that required Python modules are installed
echo "Checking required Python packages..."
check_python_module setuptools
check_python_module wheel
check_python_module twine
check_python_module build
echo "✓ All required Python packages are installed"

# Check that Git working directory is clean
echo "Checking Git working directory..."
check_git_clean
echo "✓ Git working directory is clean"

# Check that GPG key exists
echo "Checking GPG key..."
check_gpg_key "$KEY_ID"
echo "✓ GPG key '$KEY_ID' found"

# Check that remote exists (only for production releases)
if [ -n "$RELEASE_REMOTE" ]; then
    echo "Checking Git remote '$RELEASE_REMOTE'..."
    if ! git remote get-url "$RELEASE_REMOTE" &> /dev/null; then
        echo "ERROR: Git remote '$RELEASE_REMOTE' does not exist" >&2
        echo "Available remotes:" >&2
        git remote -v >&2
        exit 1
    fi
    echo "✓ Git remote '$RELEASE_REMOTE' exists"
fi

echo "=== Preflight checks passed ==="
echo ""

# Clear the dist directory
echo "Clearing the dist directory..."
rm -rf "${DIR}/dist"

# Bump version
if [ "${VERSION_SEGMENT}" == "major" ]; then
    echo "Bumping the major version..."
elif [ "${VERSION_SEGMENT}" == "minor" ]; then
    echo "Bumping the minor version..."
else
    echo "Bumping the patch version..."
fi

if [ -z "${RELEASE_URL}" ]; then
    echo "Creating version commit and tag (production mode)..."
    bumpversion "${VERSION_SEGMENT}"
else
    echo "Bumping version without commit/tag (test mode)..."
    bumpversion "${VERSION_SEGMENT}" --no-tag --no-commit
fi

echo "✓ Version bumped successfully"

# Build artifacts
echo "Building the artifacts..."
python3 -m build --sdist --wheel --outdir "${DIR}/dist"
echo "✓ Artifacts built successfully"

# Verify dist directory exists and has content
if [ ! -d "${DIR}/dist" ] || [ -z "$(ls -A "${DIR}/dist")" ]; then
    echo "ERROR: dist directory is missing or empty after build" >&2
    exit 1
fi

# Check artifacts with twine
echo "Validating artifacts with twine check..."
python3 -m twine check "${DIR}/dist/"*
echo "✓ Artifacts validated successfully"

# Sign artifacts
echo "Signing artifacts using GPG with key ${KEY_ID}..."
echo "Get your passphrase ready..."
cd "${DIR}/dist"

for file in *; do
    # Only sign regular files (not directories or links)
    if [ -f "$file" ] && [ ! -L "$file" ]; then
        echo "Signing: $file"
        gpg -a -u "${KEY_ID}" --detach-sign "$file"
    fi
done

echo "✓ Artifacts signed successfully"

# Upload to PyPI
echo "Uploading to PyPI ${RELEASE_URL:-(production)}..."
cd "${DIR}"
python3 -m twine upload ${RELEASE_URL} "${DIR}/dist/"*
echo "✓ Upload completed successfully"

# Push Git changes (only in production mode)
if [ -z "${RELEASE_URL}" ]; then
    echo "Pushing Git commit and tags to remote..."
    
    # Get current branch name and release tag
    CURRENT_BRANCH=$(git symbolic-ref --short HEAD)
    RELEASE_TAG=$(git describe --exact-match --tags HEAD)

    # Push the tags
    git push --atomic "$RELEASE_REMOTE" \
          "HEAD:refs/heads/${CURRENT_BRANCH}" \
          "refs/tags/${RELEASE_TAG}:refs/tags/${RELEASE_TAG}"
    
    echo "✓ Git commit and tags pushed successfully"
else
    echo "⚠ Skipping Git push (test mode)"
    echo "Note: Version was bumped locally but not committed to Git"
fi

echo ""
echo "=== Release completed successfully ==="
