#!/usr/bin/env bash

set -e
cd "$(dirname "$0")"

python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt

export FLASK_APP=src/app.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start the Flask application
flask run
