#!/usr/bin/env bash
# Bare-metal offline test suite for the SAR registry.
# Prefer Ubuntu 24.04 (native Python 3.12). On 22.04 add the deadsnakes PPA first.
#
# Usage (from repo root):
#   bash sar/ci-local.sh
#
# The script installs system packages with sudo, creates/reuses a .venv, installs the
# complete Python set (so microtopo and other optional suites actually run), then executes
# the full registry test suite.

set -euo pipefail

echo "==> Installing system packages (openssl, poppler-utils, GDAL, Python 3.12)"
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev build-essential \
    openssl poppler-utils libgdal-dev gdal-bin

if [[ ! -d .venv ]]; then
  echo "==> Creating .venv"
  python3.12 -m venv .venv
else
  echo "==> Reusing existing .venv"
fi

source .venv/bin/activate

echo "==> Installing Python dependencies"
pip install --upgrade pip
pip install numpy scipy rasterio piexif pillow jsonschema matplotlib scikit-learn \
    -r sar/coldtrace/backend/requirements-test.txt

echo "==> Running full suite: python3 sar/registry.py --test-all"
python3 sar/registry.py --test-all

echo "==> Done."
