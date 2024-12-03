#!/bin/bash

DB_NAME="aggregator_db"
DB_USER="aggregator"

# 1. remove contents of /app and other files/links
rm -rf /app/*
rm -f /usr/local/bin/aggregator_run_gunicorn.sh

# 2. stop services, timers and targets
systemctl stop aggregator-gunicorn.service
systemctl disable aggregator-gunicorn.service

# 3. removing app files from /etc/systemd/system/
rm -f /etc/systemd/system/aggregator-gunicorn.service
rm -f /etc/nginx/conf.d/aggregator.conf

# 4. reload systemd and other services
systemctl restart nginx
systemctl daemon-reload

# 5. remove db and user
sudo -u postgres psql -c "drop database $DB_NAME;"
sudo -u postgres psql -c "drop user $DB_USER;"

# 6. deleting user and group
userdel aggregator
groupdel aggregator-group