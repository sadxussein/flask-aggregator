"""Script for zabbix agent.

Retrieves information about hosts in oVirt."""

import json
from datetime import datetime, timedelta

from flask_aggregator.back.dbmanager import DBManager
from flask_aggregator.back.models import Host
from flask_aggregator.config import Config

def run():
    """External runner."""
    dbmanager = DBManager()
    hosts = dbmanager.get_all_data_as_dict(Host)
    latest_records = {}
    for host in hosts:
        # If host info was created more than 1 day ago we ignore it.
        if (
            host["name"] not in latest_records or
            host["time_created"] > latest_records[host["name"]]["time_created"]
        ):
            latest_records[host["name"]] = {
                "name": host["name"],
                "ip": host["ip"],
                "status": host["status"],
                "time_created": host["time_created"]
            }
    keys_to_ignore = ["time_created"]
    host_list = list(latest_records.values())
    result = [
        {
            k: v for k, v in values.items()
            if k not in keys_to_ignore
        }
        for values in latest_records.values()
    ]
    with open(
        f"{Config.ROOT_DIR}/get_hosts.json", 'w', encoding="utf-8"
    ) as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    run()
