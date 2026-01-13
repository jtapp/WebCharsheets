#!/usr/bin/env bash

set -e
cd "$(dirname "$0")"

python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt

echo "$(which python) | $(which pip)"

gunicorn -w 1 -b 127.0.0.1:7420 --chdir src/ app:app