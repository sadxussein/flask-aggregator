#!/bin/bash

# remove contents of /app and other files/links
rm -rf /app/*

# stop services, timers and targets
systemctl stop aggregator-gunicorn.service
systemctl disable aggregator-gunicorn.service
systemctl stop aggregator.target
systemctl disable aggregator.target

# removing app files from /etc
rm -f /etc/systemd/system/aggregator*.target
rm -f /etc/nginx/conf.d/aggregator.conf

# reload systemd and other services
systemctl restart nginx
systemctl daemon-reload

# if we are completely removing the aggregator server
if [[ "$1" == "--purge" ]]; then
    # remove packages
    dnf remove -y postgresql-server nginx python3-pip python3-devel gcc libxml2-devel

    # remove db and user
    DB_NAME="aggregator_db"
    DB_USER="aggregator"
    sudo -u postgres psql -c "drop database $DB_NAME;"
    sudo -u postgres psql -c "drop role $DB_USER;"
fi

# deleting user and group
userdel aggregator
groupdel aggregator-group
