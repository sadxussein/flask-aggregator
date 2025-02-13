"""Get info about backups from Cyberbackup."""

from flask_aggregator.back.cyberbackup_helper import CyberbackupHelper
from flask_aggregator.config import Config, ProductionConfig
from flask_aggregator.back.db import DBConnection, DBManager
from flask_aggregator.back.models import Backups

def run():
    """External runner."""
    # Dropping previous records.
    db_con = DBConnection(ProductionConfig.DB_URL)
    db_man = DBManager(Backups, db_con)
    db_man.truncate_table()
    # Making new records.
    for dpc in Config.CYBERBACKUP_DPC_LIST:
        cb_helper = CyberbackupHelper(dpc)
        cb_helper.add_data_as_dict()

if __name__ == "__main__":
    run()
