"""Get info about backups from Cyberbackup."""

from flask_aggregator.back.cyberbackup_helper import CyberbackupHelper
from flask_aggregator.config import Config

def run():
    """External runner."""
    for dpc in Config.CYBERBACKUP_DPC_LIST:
        cb_helper = CyberbackupHelper(dpc)
        cb_helper.add_data_as_dict()

if __name__ == "__main__":
    run()
