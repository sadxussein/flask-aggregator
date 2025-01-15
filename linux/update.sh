#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source /app/flask-aggregator/bin/activate
LATEST_WHL=$(readlink $SCRIPT_DIR/app/latest.whl)
echo "$LATEST_WHL"
pip3 install --upgrade "$LATEST_WHL"
deactivate

chown -R aggregator:aggregator-group /app
chmod -R g+rwx /app
