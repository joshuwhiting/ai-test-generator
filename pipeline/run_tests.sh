#!/usr/bin/env bash
# Runs the test suite under tests/. Used by CI; also works locally.
# Extra arguments are passed to pytest, e.g. pipeline/run_tests.sh tests/web --headed
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -m pytest -v "$@"
