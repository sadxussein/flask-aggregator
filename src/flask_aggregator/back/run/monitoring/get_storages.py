"""Script for zabbix agent.

Retrieves information about storages in oVirt."""

import json

from flask_aggregator.back.dbmanager import DBManager
from flask_aggregator.back.models import Storage
from flask_aggregator.config import Config

def run():
    """External runner."""
    dbmanager = DBManager()
    storages = dbmanager.get_all_data_as_dict(Storage)
    result = {"storage_domain": []}
    for storage in storages:
        s = {
            "cluster": storage["engine"],
            "name": storage["name"],
            "id": str(storage["uuid"]),
            "available": storage["available"],
            "used": storage["used"],
            "committed": storage["committed"],
            "type": "data",
            "warning_low_space_indicator": 10
        }
        result["storage_domain"].append(s)
    if result:
        with open(
            f"{Config.ROOT_DIR}/get_storages.json", 'w', encoding="utf-8"
        ) as file:
            json.dump(result, file, indent=4, ensure_ascii=False)
    # print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    run()
