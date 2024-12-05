#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source /app/flask-aggregator/bin/activate
pip3 install --upgrade $SCRIPT_DIR/app/flask_aggregator*.whl
deactivate

chown -R aggregator:aggregator-group /app
chmod -R g+rx /app
