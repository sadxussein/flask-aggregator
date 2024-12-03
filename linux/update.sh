#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source /app/flask-aggregator/bin/activate
pip3 install --force-reinstall $SCRIPT_DIR/app/flask_aggregator*.whl

systemctl restart aggregator-gunicorn.service