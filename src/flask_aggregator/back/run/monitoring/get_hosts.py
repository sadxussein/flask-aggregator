"""Script for zabbix agent.

Retrieves information about hosts in oVirt."""

from flask_aggregator.back.dbmanager import DBManager
from flask_aggregator.back.models import Host

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
    print(result)

if __name__ == "__main__":
    run()
