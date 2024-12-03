#!/bin/bash

source /app/flask-aggregator/bin/activate
which python3
gunicorn -w 10 -b 127.0.0.1:8000 flask_aggregator.front.app:app
