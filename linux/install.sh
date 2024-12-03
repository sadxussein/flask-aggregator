#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_NAME="aggregator_db"
DB_USER="aggregator"
DB_PASS="68mLMd4WzqLQkZ1LXPd0"

# 1. set up user and folder rights
groupadd aggregator-group
useradd -M -s /sbin/nologin aggregator
usermod -aG aggregator-group aggregator

# 2. set up venv
mkdir -p /app/flask-aggregator
mkdir -p /app/log/nginx
python3 -m venv /app/flask-aggregator
source /app/flask-aggregator/bin/activate

# 3. install python packages to venv
pip3 install -r $SCRIPT_DIR/app/requirements.txt
pip3 install --force-reinstall $SCRIPT_DIR/app/flask_aggregator*.whl

# 4. copy runner scripts
cp $SCRIPT_DIR/app/run.sh /app/run.sh
chmod +x /app/run.sh
ln -s /app/run.sh /usr/local/bin/aggregator_run_gunicorn.sh

# 4. change rights to /app folder
chown -R aggregator:aggregator /app

# 5. set up targets, timers and services
cp $SCRIPT_DIR/etc/systemd/system/aggregator-gunicorn.service /etc/systemd/system/aggregator-gunicorn.service

# 6. reload systemd
systemctl daemon-reload

# 7. start gunicorn service
systemctl start aggregator-gunicorn.service
systemctl enable aggregator-gunicorn.service

# 8. set up nginx config
cp $SCRIPT_DIR/etc/nginx/conf.d/aggregator.conf /etc/nginx/conf.d/aggregator.conf

# 9. restart nginx service
systemctl enable nginx
systemctl restart nginx

# 10. set up postgresql config (user, pass, db)
sudo -u postgres psql -c "create database $DB_NAME;"
sudo -u postgres psql -c "create user $DB_USER with password '$DB_PASS';"
sudo -u postgres psql -c "alter database $DB_NAME owner to $DB_USER;"
# sudo -u postgres psql -c "grant all privileges on schema public to $DB_USER;"
sudo -u postgres psql -c "grant all privileges on database $DB_NAME to $DB_USER;"

# 10. set up service for host monitoring
# 11. set up timer for host monitoring
# 12. set up service for storage monitoring
# 13. set up timer for storage monitoring
