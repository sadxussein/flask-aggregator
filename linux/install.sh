#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# setting up http proxy environment for python
export HTTPS_PROXY=http://usergate5.crimea.rncb.ru:8090/
export HTTP_PROXY=http://usergate5.crimea.rncb.ru:8090/

# install zabbix-agent, postgresql, nginx
dnf install -y zabbix-agent postgresql-server nginx python3-pip
if [ $? -ne 0 ]; then
    echo "Failed to install required packages. Aborting."
    exit 1
fi
postgresql-setup --initdb
systemctl start zabbix-agent postgresql nginx
systemctl enable zabbix-agent postgresql nginx

# set up user and folder rights
groupadd aggregator-group
useradd -M -s /sbin/nologin aggregator
usermod -aG aggregator-group aggregator

# set up venv
mkdir -p /app/flask-aggregator
mkdir -p /app/log/nginx
cp $SCRIPT_DIR/app/.env /app/.env
python3 -m venv /app/flask-aggregator
source /app/flask-aggregator/bin/activate

# install python packages to venv
pip3 install -r $SCRIPT_DIR/app/requirements.txt
pip3 install --force-reinstall $SCRIPT_DIR/app/latest.whl

# change rights to /app folder
chown -R aggregator:aggregator-group /app
chmod -R g+rx /app/*

# set up targets, timers and services
cp $SCRIPT_DIR/etc/systemd/system/aggregator-gunicorn.service /etc/systemd/system/aggregator-gunicorn.service
cp $SCRIPT_DIR/etc/systemd/system/aggregator.target /etc/systemd/system/aggregator.target
cp $SCRIPT_DIR/etc/systemd/system/aggregator-collector-hosts.service /etc/systemd/system/aggregator-collector-hosts.service
cp $SCRIPT_DIR/etc/systemd/system/aggregator-collector-hosts.timer /etc/systemd/system/aggregator-collector-hosts.timer
cp $SCRIPT_DIR/etc/systemd/system/aggregator-collector-storages.service /etc/systemd/system/aggregator-collector-storages.service
cp $SCRIPT_DIR/etc/systemd/system/aggregator-collector-storages.timer /etc/systemd/system/aggregator-collector-storages.timer
cp $SCRIPT_DIR/etc/systemd/system/aggregator-collector-backups.service /etc/systemd/system/aggregator-collector-backups.service
cp $SCRIPT_DIR/etc/systemd/system/aggregator-collector-backups.timer /etc/systemd/system/aggregator-collector-backups.timer

# reload systemd
systemctl daemon-reload

# start and enable main timer target and service
systemctl start aggregator-gunicorn.service
systemctl enable aggregator-gunicorn.service
systemctl start aggregator.target
systemctl enable aggregator.target

# set up nginx config
cp $SCRIPT_DIR/etc/nginx/conf.d/aggregator.conf /etc/nginx/conf.d/aggregator.conf

# restart nginx service
systemctl enable nginx
systemctl restart nginx

# set up postgresql config (user, pass, db)
DB_NAME="aggregator_db"
DB_USER="aggregator"
sudo -u postgres psql -c "create database $DB_NAME;"
sudo -u postgres psql -c "create user $DB_USER with password '$DB_PASS';"
sudo -u postgres psql -c "alter database $DB_NAME owner to $DB_USER;"
sudo -u postgres psql -c "grant all privileges on database $DB_NAME to $DB_USER;"

# deactivating environment
deactivate
