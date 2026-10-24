#!/usr/bin/env bash
# Bare-metal offline test suite for the SAR registry.
# Prefer Ubuntu 24.04 (native Python 3.12). On 22.04 add the deadsnakes PPA first.
#
# Usage (from repo root):
#   bash sar/ci-local.sh

set -euo pipefail

sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev build-essential \
    openssl poppler-utils libgdal-dev gdal-bin

python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install numpy scipy rasterio piexif pillow jsonschema matplotlib scikit-learn \
    -r sar/coldtrace/backend/requirements-test.txt

python3 sar/registry.py --test-all
