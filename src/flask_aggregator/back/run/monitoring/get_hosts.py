"""Script for zabbix agent.

Retrieves information about hosts in oVirt."""

import json

from flask_aggregator.back.dbmanager import DBManager
from flask_aggregator.back.models import Host
from flask_aggregator.config import Config

def run():
    """External runner."""
    dbmanager = DBManager()
    hosts = dbmanager.get_all_data_as_dict(Host)
    result = []
    for host in hosts:
        h = {
            "name": host["name"],
            "ip": host["ip"],
            "status": host["status"]
        }
        result.append(h)
    if result:
        with open(
            f"{Config.ROOT_DIR}/get_hosts.json", 'w', encoding="utf-8"
        ) as file:
            json.dump(result, file, indent=4, ensure_ascii=False)
    # print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    run()
