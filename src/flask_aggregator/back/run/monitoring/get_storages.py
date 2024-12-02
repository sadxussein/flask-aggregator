"""Script for zabbix agent.

Retrieves information about storages in oVirt."""

from src.flask_aggregator.back.dbmanager import DBManager
from src.flask_aggregator.back.models import Storage

if __name__ == "__main__":
    dbmanager = DBManager()
    print(dbmanager.get_all_data_as_dict(Storage))
