#!/bin/bash

# 1. set up user and folder rights
groupadd aggregator-group
useradd -s /bin/bash aggregator
usermod -aG aggregator-group aggregator

# 2. set up venv
mkdir -p /app/flask-aggregator
python3 -m venv /app/flask-aggregator
source /app/flask-aggregator/bin/activate

# 3. install python packages to venv
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pip3 install -r $SCRIPT_DIR/app/requirements.txt
pip3 install --force-reinstall $SCRIPT_DIR/app/flask_aggregator*.whl

# 4. copy runner scripts
cp $SCRIPT_DIR/app/run.sh /app/run.sh
chmod +x /app/run.sh
ln -s /app/run.sh /usr/local/bin/aggregator_run_gunicorn.sh

# 4. change rights to /app folder
chown -R aggregator:aggregator /app

# 5. set up targets, timers and services
cp etc/systemd/system/aggregator-gunicorn.service /etc/systemd/system/aggregator-gunicorn.service

# 6. reload systemd
systemctl daemon-reload

# 6. start gunicorn service
systemctl start aggregator-gunicorn.service
systemctl enable aggregator-gunicorn.service
# 6. set up nginx config
# 7. restart nginx service
# 8. set up postgresql config (user, pass, port, db)
# 9. restart postgresql
# 10. set up service for host monitoring
# 11. set up timer for host monitoring
# 12. set up service for storage monitoring
# 13. set up timer for storage monitoring
