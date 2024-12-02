"""Script for zabbix agent.

Retrieves information about hosts in oVirt."""

from src.flask_aggregator.back.dbmanager import DBManager
from src.flask_aggregator.back.models import Host

if __name__ == "__main__":
    dbmanager = DBManager()
    print(dbmanager.get_all_data_as_dict(Host))
