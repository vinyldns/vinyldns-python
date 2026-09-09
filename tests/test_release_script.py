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

import os
import shutil
import subprocess
from pathlib import Path


def create_fake_python3(bin_dir: Path, log_file: Path, release_test_fail) -> None:
    """Create a fake python3 executable that handles version probes, import checks,
    and records -m build and -m twine invocations."""

    fake_python = bin_dir / "python3"
    fake_python.write_text(f'''#!/usr/bin/env bash
set -e

RELEASE_TEST_FAIL={release_test_fail}
LOG_FILE="{log_file}"

# Log all invocations
echo "python3 $@" >> "$LOG_FILE"

# Handle version check
if [[ "$RELEASE_TEST_FAIL" == "python-version" ]]; then
    if [[ "$1" == "-c" ]] && [[ "$2" == *"sys.version_info"* ]]; then
        echo "2.7"  # Unsupported version
        exit 0
    fi
elif [[ "$1" == "-c" ]] && [[ "$2" == *"sys.version_info"* ]]; then
    echo "3.11"
    exit 0
fi

# Handle import checks
if [[ "$RELEASE_TEST_FAIL" == "missing-dependencies" ]]; then
    if [[ "$1" == "-c" ]] && [[ "$2" == *"import "* ]]; then
        echo "ERROR: Missing dependency" >&2
        exit 1
    fi
elif [[ "$1" == "-c" ]] && [[ "$2" == *"import "* ]]; then
    exit 0
fi

# Handle -m build

if [[ "$RELEASE_TEST_FAIL" == "build" ]]; then
    if [[ "$1" == "-m" ]] && [[ "$2" == "build" ]]; then
        echo "ERROR: Build failed" >&2
        exit 1
    fi
else
    if [[ "$1" == "-m" ]] && [[ "$2" == "build" ]]; then
        mkdir -p dist
        touch dist/vinyldns-python-0.9.11-py3-none-any.whl
        touch dist/vinyldns-python-0.9.11.tar.gz
        echo "SUCCESS: Build succeeded" >&2
        exit 0
    fi
fi

# Handle -m twine
if [[ "$RELEASE_TEST_FAIL" == "twine-check" ]]; then
    if [[ "$1" == "-m" ]] && [[ "$2" == "twine" ]] && [[ "$3" == "check" ]]; then
        echo "ERROR: twine check error" >&2
        exit 1
    elif [[ "$1" == "-m" ]] && [[ "$2" == "twine" ]] && [[ "$3" == "upload" ]]; then
        echo "ERROR: twine upload should not happen after failed twine check" >&2
        exit 1
    fi
elif [[ "$RELEASE_TEST_FAIL" == "twine-upload" ]]; then
    if [[ "$1" == "-m" ]] && [[ "$2" == "twine" ]] && [[ "$3" == "check" ]]; then
        echo "SUCCESS: Twine check passed" >&2
        exit 0
    elif [[ "$1" == "-m" ]] && [[ "$2" == "twine" ]] && [[ "$3" == "upload" ]]; then
        echo "ERROR: Twine upload failed" >&2
        exit 1
    fi
elif [[ "$RELEASE_TEST_FAIL" == "build" ]]; then
    if [[ "$1" == "-m" ]] && [[ "$2" == "twine" ]]; then
        echo "ERROR: Twine check should not happen after failed build" >&2
        exit 1
    fi
else
    if [[ "$1" == "-m" ]] && [[ "$2" == "twine" ]] && [[ "$3" == "check" ]]; then
        echo "SUCCESS: Twine check passed" >&2
        exit 0
    elif [[ "$1" == "-m" ]] && [[ "$2" == "twine" ]] && [[ "$3" == "upload" ]]; then
        echo "SUCCESS: Twine upload passed" >&2
        exit 0
    elif [[ "$1" == "-m" ]] && [[ "$2" == "twine" ]]; then
        echo "ERROR: Unknown twine subcommand: $3" >&2
        exit 1
    fi
fi

# Default: unknown invocation
echo "ERROR: Unknown python3 invocation: $@" >&2
exit 1
''', encoding='utf-8')
    fake_python.chmod(0o755)


def create_fake_git(bin_dir: Path, log_file: Path, release_test_fail) -> None:
    """Create a fake git executable that handles status, remote, and push commands."""

    fake_git = bin_dir / "git"
    fake_git.write_text(f'''#!/usr/bin/env bash

LOG_FILE="{log_file}"
RELEASE_TEST_FAIL={release_test_fail}

# Log all invocations
echo "git $@" >> "$LOG_FILE"

case "$1" in
    status)
        if [[ "$2" == "--porcelain" ]]; then
            if [[ "$RELEASE_TEST_FAIL" == "dirty-tree" ]]; then
                # Return output indicating uncommitted changes
                echo " M some-file.py"
                exit 0
            else
                # Return empty output (clean working directory)
                exit 0
            fi
        elif [[ "$2" == "--short" ]]; then
            exit 0
        fi
        ;;
    remote)
        if [[ "$2" == "get-url" ]]; then
            # Pretend the remote exists
            echo "https://github.com/vinyldns/vinyldns-python.git"
            exit 0
        elif [[ "$2" == "-v" ]]; then
            echo "origin\thttps://github.com/vinyldns/vinyldns-python.git (fetch)"
            echo "origin\thttps://github.com/vinyldns/vinyldns-python.git (push)"
            exit 0
        fi
        ;;
    symbolic-ref)
        if [[ "$2" == "--short" ]] && [[ "$3" == "HEAD" ]]; then
            echo "main"
            exit 0
        fi
        ;;
    describe)
        if [[ "$2" == "--exact-match" ]] && [[ "$3" == "--tags" ]]; then
            echo "v0.9.11"
            exit 0
        fi
        ;;
    push)
        if [[ "$RELEASE_TEST_FAIL" == "git-push" ]]; then
            echo "ERROR: git push failed" >&2
            exit 1
        elif [[ "$RELEASE_TEST_FAIL" == "twine-upload" ]] || [[ "$RELEASE_TEST_FAIL" == "gpg-sign" ]] || \
             [[ "$RELEASE_TEST_FAIL" == "twine-check" ]] || [[ "$RELEASE_TEST_FAIL" == "build" ]]; then
            # Forbidden operation - fail immediately
            echo "ERROR: git push should not be called in this test" >&2
            exit 1
        else
            exit 0
        fi
        ;;
esac

# Default: unknown invocation
echo "ERROR: Unknown git invocation: $@" >&2
exit 1
''', encoding='utf-8')
    fake_git.chmod(0o755)


def create_fake_gpg(bin_dir: Path, log_file: Path, release_test_fail) -> None:
    """Create a fake gpg executable that handles key checks and signing."""

    fake_gpg = bin_dir / "gpg"
    fake_gpg.write_text(f'''#!/usr/bin/env bash

LOG_FILE="{log_file}"
RELEASE_TEST_FAIL={release_test_fail}

# Log all invocations
echo "gpg $@" >> "$LOG_FILE"

# Handle --list-secret-keys (preflight check)
if [[ "$1" == "--list-secret-keys" ]]; then
    if [[ "$RELEASE_TEST_FAIL" == "missing-gpg-key" ]]; then
        echo "ERROR: GPG key not found" >&2
        exit 2
    else
        # Just succeed - key exists
        exit 0
    fi
fi

# Handle signing with --detach-sign
if [[ "$RELEASE_TEST_FAIL" == "twine-check" ]] || [[ "$RELEASE_TEST_FAIL" == "build" ]] || \
   [[ "$RELEASE_TEST_FAIL" == "missing-dependencies" ]] || [[ "$RELEASE_TEST_FAIL" == "python-version" ]] || \
   [[ "$RELEASE_TEST_FAIL" == "dirty-tree" ]] || [[ "$RELEASE_TEST_FAIL" == "missing-gpg-key" ]]; then
    if [[ "$2" == "-u" ]] && [[ "$4" == "--detach-sign" ]]; then
        # Forbidden operation - fail immediately
        echo "ERROR: gpg --detach-sign should not be called in this test (preflight failed)" >&2
        exit 1
    fi
elif [[ "$RELEASE_TEST_FAIL" == "gpg-sign" ]]; then
    if [[ "$2" == "-u" ]] && [[ "$4" == "--detach-sign" ]]; then
        # Force fail
        echo "ERROR: gpg --detach-sign error" >&2
        exit 1
    fi
else
    if [[ "$2" == "-u" ]] && [[ "$4" == "--detach-sign" ]]; then
            # Simulate detached signature output produced by gpg.
            touch "$5.asc"
            echo "SUCCESS: gpg --detach-sign" >&2
            exit 0
    fi
fi
# Default: unknown invocation
echo "ERROR: Unknown gpg invocation: $@" >&2
exit 1
''', encoding='utf-8')
    fake_gpg.chmod(0o755)


def create_fake_bumpversion(bin_dir: Path, log_file: Path) -> None:
    """Create a fake bumpversion executable that simulates version bumping."""

    fake_bumpversion = bin_dir / "bumpversion"
    fake_bumpversion.write_text(f'''#!/usr/bin/env bash
set -e

LOG_FILE="{log_file}"

# Log all invocations
echo "bumpversion $@" >> "$LOG_FILE"

# Simulate successful version bump
exit 0
''', encoding='utf-8')
    fake_bumpversion.chmod(0o755)


def run_release(tmp_path, fail_at, production=False, remote_name="test-remote"):
    """Run release.sh with fake executables and configurable mode flags."""

    # Setup test directory structure
    test_dir = tmp_path / "test_release_script"
    test_dir.mkdir()

    # Create bin directory for fake executables
    bin_dir = test_dir / "bin"
    bin_dir.mkdir()

    # Create shared log file
    log_file = test_dir / "command.log"
    log_file.touch()

    # Create fake executables
    create_fake_python3(bin_dir, log_file, fail_at)
    create_fake_git(bin_dir, log_file, fail_at)
    create_fake_gpg(bin_dir, log_file, fail_at)
    create_fake_bumpversion(bin_dir, log_file)

    # Copy release.sh to test directory
    project_root = Path(__file__).parent.parent
    release_script = project_root / "release.sh"
    test_release_script = test_dir / "release.sh"
    shutil.copy(release_script, test_release_script)
    test_release_script.chmod(0o755)

    # Copy required files for the script
    for file_name in ["setup.py", "setup.cfg", "README.md"]:
        src_file = project_root / file_name
        if src_file.exists():
            shutil.copy(src_file, test_dir / file_name)

    # Copy src directory structure (required for build)
    src_dir = project_root / "src"
    if src_dir.exists():
        shutil.copytree(src_dir, test_dir / "src")

    # Prepare environment
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["RELEASE_TEST_LOG"] = str(log_file)

    command = ["bash", str(test_release_script), "--key-id", "test-key-123"]
    if production:
        command.extend(["--production", "--remote", remote_name])


    # Run release.sh with explicit mode flags.
    result = subprocess.run(
        command,
        cwd=test_dir,
        env=env,
        capture_output=True,
        text=True
    )

    print("=== release.sh stdout ===")
    print(result.stdout)
    print("=== release.sh stderr ===")
    print(result.stderr)
    print("=== stub command log ===")
    print(log_file.read_text())

    return result, log_file.read_text()


def test_failed_build_stops_release(tmp_path):
    """Test that when python3 -m build fails, the script stops and does not proceed."""
    fail_at = 'build'
    result, command_log = run_release(tmp_path, fail_at)

    # Assertions:

    # 1. Script should return nonzero exit code (build failed)
    assert result.returncode != 0, \
        f"Expected nonzero exit code, got {result.returncode}"

    # 2. Build was attempted
    assert "python3 -m build" in command_log, \
        f"Expected 'python3 -m build' in log, but found:\n{command_log}"

    # 3. No GPG signing invocation (--detach-sign)
    # Note: --list-secret-keys is expected for preflight check
    gpg_sign_commands = [line for line in command_log.split('\n')
                         if 'gpg' in line and '--detach-sign' in line]
    assert len(gpg_sign_commands) == 0, \
        f"Expected no GPG signing, but found:\n{chr(10).join(gpg_sign_commands)}"

    # 4. No twine check or upload invocation
    twine_commands = [line for line in command_log.split('\n')
                      if 'python3 -m twine' in line]
    assert len(twine_commands) == 0, \
        f"Expected no twine invocations, but found:\n{chr(10).join(twine_commands)}"

    # 5. No git push invocation
    # Note: git status and other preflight calls are expected
    git_push_commands = [line for line in command_log.split('\n')
                         if 'git push' in line]
    assert len(git_push_commands) == 0, \
        f"Expected no 'git push', but found:\n{chr(10).join(git_push_commands)}"

    # 6. Script does not print successful-completion message
    assert "Release completed successfully" not in result.stdout, \
        f"Expected no success message, but stdout contains:\n{result.stdout}"
    assert "Release completed successfully" not in result.stderr, \
        f"Expected no success message, but stderr contains:\n{result.stderr}"


def test_failed_twine_check_stops_release(tmp_path):
    """Test that when python3 -m twine check fails, the script stops and does not proceed."""
    fail_at = 'twine-check'
    result, command_log = run_release(tmp_path, fail_at)

    # Assertions:

    # 1. Script should return nonzero exit code (twine-check failed)
    assert result.returncode != 0, \
        f"Expected nonzero exit code, got {result.returncode}"

    # 2. Twine check was attempted
    assert "python3 -m twine check" in command_log, \
        f"Expected 'python3 -m twine check' in log, but found:\n{command_log}"

    # 3. No GPG signing invocation (--detach-sign)
    # Note: --list-secret-keys is expected for preflight check
    gpg_sign_commands = [line for line in command_log.split('\n')
                         if 'gpg' in line and '--detach-sign' in line]
    assert len(gpg_sign_commands) == 0, \
        f"Expected no GPG signing, but found:\n{chr(10).join(gpg_sign_commands)}"

    # 4. No twine upload invocation
    twine_commands = [line for line in command_log.split('\n')
                      if 'python3 -m twine upload' in line]
    assert len(twine_commands) == 0, \
        f"Expected no twine upload, but found:\n{chr(10).join(twine_commands)}"

    # 5. No git push invocation
    # Note: git status and other preflight calls are expected
    git_push_commands = [line for line in command_log.split('\n')
                         if 'git push' in line]
    assert len(git_push_commands) == 0, \
        f"Expected no 'git push', but found:\n{chr(10).join(git_push_commands)}"

    # 6. Script does not print successful-completion message
    assert "Release completed successfully" not in result.stdout, \
        f"Expected no success message, but stdout contains:\n{result.stdout}"
    assert "Release completed successfully" not in result.stderr, \
        f"Expected no success message, but stderr contains:\n{result.stderr}"


def test_failed_gpg_sign_stops_release(tmp_path):
    """Test that when gpg sign fails, the script stops and does not proceed."""
    fail_at = 'gpg-sign'
    result, command_log = run_release(tmp_path, fail_at)

    # Assertions:

    # 1. Script should return nonzero exit code (twine-check failed)
    assert result.returncode != 0, \
        f"Expected nonzero exit code, got {result.returncode}"

    # 2. GPG signing was attempted
    assert [line for line in command_log.split('\n')
            if 'gpg' in line and '--detach-sign' in line], \
        f"Expected 'gpg and --detach-sign' in log, but found:\n{command_log}"

    # 3. No twine upload invocation
    twine_commands = [line for line in command_log.split('\n')
                      if 'python3 -m twine upload' in line]
    assert len(twine_commands) == 0, \
        f"Expected no twine upload, but found:\n{chr(10).join(twine_commands)}"

    # 4. No git push invocation
    # Note: git status and other preflight calls are expected
    git_push_commands = [line for line in command_log.split('\n')
                         if 'git push' in line]
    assert len(git_push_commands) == 0, \
        f"Expected no 'git push', but found:\n{chr(10).join(git_push_commands)}"

    # 5. Script does not print successful-completion message
    assert "Release completed successfully" not in result.stdout, \
        f"Expected no success message, but stdout contains:\n{result.stdout}"
    assert "Release completed successfully" not in result.stderr, \
        f"Expected no success message, but stderr contains:\n{result.stderr}"


def test_failed_twine_upload_stops_release(tmp_path):
    """Test that a failed twine upload in production mode prevents git push."""
    fail_at = 'twine-upload'
    result, command_log = run_release(tmp_path, fail_at, production=True, remote_name="test-remote")

    # Assertions:

    # 1. Script should return nonzero exit code (twine upload failed)
    assert result.returncode != 0, \
        f"Expected nonzero exit code, got {result.returncode}"

    # 2. Twine upload was attempted
    assert "python3 -m twine upload" in command_log, \
        f"Expected 'python3 -m twine upload' in log, but found:\n{command_log}"

    # 3. Production mode should have validated the configured remote.
    assert "git remote get-url test-remote" in command_log, \
        f"Expected production remote validation in log, but found:\n{command_log}"

    # 4. No git push invocation
    git_push_commands = [line for line in command_log.split('\n')
                         if 'git push' in line]
    assert len(git_push_commands) == 0, \
        f"Expected no 'git push', but found:\n{chr(10).join(git_push_commands)}"

    # 5. Script does not print successful-completion message
    assert "Release completed successfully" not in result.stdout, \
        f"Expected no success message, but stdout contains:\n{result.stdout}"
    assert "Release completed successfully" not in result.stderr, \
        f"Expected no success message, but stderr contains:\n{result.stderr}"


def test_production_release_pushes_with_atomic_git_push(tmp_path):
    """Test that a successful production release uses atomic git push."""
    fail_at = 'none'
    result, command_log = run_release(tmp_path, fail_at, production=True, remote_name="test-remote")

    # 1. Script should succeed.
    assert result.returncode == 0, \
        f"Expected zero exit code, got {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"

    # 2. Production mode remote validation should run.
    assert "git remote get-url test-remote" in command_log, \
        f"Expected production remote validation in log, but found:\n{command_log}"

    # 3. Atomic git push should be attempted to the configured remote.
    assert "git push --atomic test-remote" in command_log, \
        f"Expected atomic git push in log, but found:\n{command_log}"

    # 4. Upload should include signature files generated by gpg.
    upload_commands = [line for line in command_log.split('\n')
                       if 'python3 -m twine upload' in line]
    assert upload_commands, f"Expected twine upload command, but found:\n{command_log}"
    assert any('.asc' in line for line in upload_commands), \
        f"Expected twine upload to include signature artifacts, but found:\n{chr(10).join(upload_commands)}"


def test_missing_dependencies_stops_release(tmp_path):
    """Test that missing Python dependencies stop the release before version changes."""
    fail_at = 'missing-dependencies'
    result, command_log = run_release(tmp_path, fail_at)

    # Assertions:

    # 1. Script should return nonzero exit code (dependency check failed)
    assert result.returncode != 0, \
        f"Expected nonzero exit code, got {result.returncode}"

    # 2. Import check was attempted
    assert "import " in command_log, \
        f"Expected import check in log, but found:\n{command_log}"

    # 3. No build invocation
    assert "python3 -m build" not in command_log, \
        f"Expected no build, but found:\n{command_log}"

    # 4. No bumpversion invocation
    bumpversion_commands = [line for line in command_log.split('\n')
                            if 'bumpversion' in line]
    assert len(bumpversion_commands) == 0, \
        f"Expected no bumpversion, but found:\n{chr(10).join(bumpversion_commands)}"

    # 5. Script does not print successful-completion message
    assert "Release completed successfully" not in result.stdout, \
        f"Expected no success message, but stdout contains:\n{result.stdout}"


def test_unsupported_python_version_stops_release(tmp_path):
    """Test that an unsupported Python version stops the release before version changes."""
    fail_at = 'python-version'
    result, command_log = run_release(tmp_path, fail_at)

    # Assertions:

    # 1. Script should return nonzero exit code (version check failed)
    assert result.returncode != 0, \
        f"Expected nonzero exit code, got {result.returncode}"

    # 2. Version check was attempted
    assert "sys.version_info" in command_log, \
        f"Expected version check in log, but found:\n{command_log}"

    # 3. No build invocation
    assert "python3 -m build" not in command_log, \
        f"Expected no build, but found:\n{command_log}"

    # 4. No bumpversion invocation
    bumpversion_commands = [line for line in command_log.split('\n')
                            if 'bumpversion' in line]
    assert len(bumpversion_commands) == 0, \
        f"Expected no bumpversion, but found:\n{chr(10).join(bumpversion_commands)}"

    # 5. Script does not print successful-completion message
    assert "Release completed successfully" not in result.stdout, \
        f"Expected no success message, but stdout contains:\n{result.stdout}"


def test_dirty_working_tree_stops_release(tmp_path):
    """Test that a dirty working tree stops the release before version changes."""
    fail_at = 'dirty-tree'
    result, command_log = run_release(tmp_path, fail_at)

    # Assertions:

    # 1. Script should return nonzero exit code (git status check failed)
    assert result.returncode != 0, \
        f"Expected nonzero exit code, got {result.returncode}"

    # 2. Git status check was attempted
    assert "git status" in command_log, \
        f"Expected 'git status' in log, but found:\n{command_log}"

    # 3. No build invocation
    assert "python3 -m build" not in command_log, \
        f"Expected no build, but found:\n{command_log}"

    # 4. No bumpversion invocation
    bumpversion_commands = [line for line in command_log.split('\n')
                            if 'bumpversion' in line]
    assert len(bumpversion_commands) == 0, \
        f"Expected no bumpversion, but found:\n{chr(10).join(bumpversion_commands)}"

    # 5. Script does not print successful-completion message
    assert "Release completed successfully" not in result.stdout, \
        f"Expected no success message, but stdout contains:\n{result.stdout}"


def test_missing_gpg_key_stops_release(tmp_path):
    """Test that a missing GPG key stops the release before version changes."""
    fail_at = 'missing-gpg-key'
    result, command_log = run_release(tmp_path, fail_at)

    # Assertions:

    # 1. Script should return nonzero exit code (GPG key check failed)
    assert result.returncode != 0, \
        f"Expected nonzero exit code, got {result.returncode}"

    # 2. GPG key check was attempted
    assert "gpg --list-secret-keys" in command_log, \
        f"Expected 'gpg --list-secret-keys' in log, but found:\n{command_log}"

    # 3. No build invocation
    assert "python3 -m build" not in command_log, \
        f"Expected no build, but found:\n{command_log}"

    # 4. No bumpversion invocation
    bumpversion_commands = [line for line in command_log.split('\n')
                            if 'bumpversion' in line]
    assert len(bumpversion_commands) == 0, \
        f"Expected no bumpversion, but found:\n{chr(10).join(bumpversion_commands)}"

    # 5. Script does not print successful-completion message
    assert "Release completed successfully" not in result.stdout, \
        f"Expected no success message, but stdout contains:\n{result.stdout}"
