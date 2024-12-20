#!/bin/bash

PROJECT_PATH="/home/krasnoschekovvd/flask-aggregator"
CURRENT_TAG="$(git describe --tags --abbrev=0 2>/dev/null)"

if [ -z "$CURRENT_TAG" ]; then
    echo "[ERROR] No tag applied to build. Aborting."
    exit 1
else
    source $PROJECT_PATH/venv/bin/activate
    python3 -m build -o $PROJECT_PATH/linux/app/
    deactivate
    ln -s $PROJECT_PATH/linux/app/flask_aggregator-$CURRENT_TAG-py3-none-any.whl $PROJECT_PATH/linux/app/latest.whl
    ln -s $PROJECT_PATH/linux/app/flask_aggregator-$CURRENT_TAG.tar.gz $PROJECT_PATH/linux/app/latest.tar.gz
fi
