"""Module for all get_ functions for external use."""

import os
import uuid

from flask_aggregator.back.cyberbackup_helper import (
    CBHelper,
    set_cb_servers_data,
)
from flask_aggregator.back.db import DBConnection, DBManager
from flask_aggregator.back.elma_helper import ElmaHelper
from flask_aggregator.back.models import Backups, CyberbackupAlert
from flask_aggregator.back.logger import Logger
from flask_aggregator.config import Config, DevelopmentConfig, ProductionConfig

LOCAL_DB_URL = (
    DevelopmentConfig.DB_URL
    if os.getenv("FA_ENV") == "dev"
    else ProductionConfig.DB_URL
)
LOGGER = Logger()

def get_elma_vm_access_doc() -> None:
    """Collect VmAccessDoc from elma API.

    Table with information about VM documents will be upserted to
    `elma_vm_access_doc` table.
    """
    elma_helper = ElmaHelper()
    elma_helper.import_vm_access_doc()


def init_db_tables():
    """Aggregated function for critical table initialization.

    It is paramount for system to have tables 'ovirt_engines' and
    'cyberbackup_servers' non-empty, since these values are used (or will be
    used) as foreign keys for most part of other tables.
    """
    set_cb_servers_data()
    __init_ovirt_engines_table()
    # Create tables if they are absent.
    # If tables are empty put info in them.


def __init_ovirt_engines_table():
    pass
    # Get list of ovirt engines from config.
    # Add them to the table.


def collect_cb_alerts():
    """Get data from 'alert' tables in Cyberbackups."""
    data_for_insert = []
    for srv in Config.CYBERBACKUP:
        db_password = None
        if srv["name"] == "e15":
            db_password = os.getenv("CB_DB_PASS_E15")
        elif srv["name"] in ["k45", "n32"]:
            db_password = os.getenv("CB_DB_PASS_N32_K45")
        if db_password is not None:
            cbh = CBHelper(
                f"postgresql+psycopg2://"
                f"{srv['user']}:"
                f"{db_password}@"
                f"{srv['ip']}:"
                f"{srv['port']}/"
                "cyberprotect_alert_manager"
            )
            raw_data = cbh.get_all_data("alert")
            
            # Transform data fields from remote database for local.
            for el in raw_data:
                alert_row = CyberbackupAlert(server=srv["name"])
                for k in el._fields:
                    if k != "id" and k in dir(CyberbackupAlert):
                        setattr(alert_row, k, getattr(el, k))
                data_for_insert.append(alert_row)
        else:
            raise ValueError("Failed to get CB password from ENV.")
    # Adding data to target local table.
    dbm = DBManager(CyberbackupAlert, DBConnection(LOCAL_DB_URL))
    # Since we don't need history of alerts, rather that alerts themselves
    # being present, we drop all data from table before reinserting it.
    dbm.truncate_table()
    dbm.add_data(data_for_insert)
    # TODO: add logic for file creation, that zabbix can read.
    # Is it necessary though?


def get_backups():
    """Backups collector.

    Gets data from Cyberbackup servers. Storing result in 'backups' table."""
    data = []
    for srv in Config.CYBERBACKUP:
        db_password = None
        if srv["name"] == "e15":
            db_password = os.getenv("CB_DB_PASS_E15")
        elif srv["name"] in ["k45", "n32"]:
            db_password = os.getenv("CB_DB_PASS_N32_K45")
        if db_password is not None:
            cbh = CBHelper(
                f"postgresql+psycopg2://"
                f"{srv['user']}:"
                f"{db_password}@"
                f"{srv['ip']}:"
                f"{srv['port']}/"
                "cyberprotect_vault_manager"
            )
            raw_data = cbh.get_latest_backups()
            LOGGER.log_debug(
                f"Collected {len(raw_data)} from {srv['name']} Cyberbackup."
            )
            for row in raw_data:
                namespace = uuid.UUID("12345678-1234-1234-1234-123456789123")
                upstert_uuid = uuid.uuid5(
                    namespace, f"{row[0]}-{row[2]}-{row[3]}"
                )
                db_el = Backups(
                    name=row[0],
                    uuid=upstert_uuid,
                    backup_server=srv["name"],
                    resource_ids=row[1],
                    created=row[2],
                    created_time=row[3],
                    size=row[4],
                    source_key=row[5],
                    disks=row[6],
                    type=row[7],
                )
                data.append(db_el)
    # Dropping previous records and adding new data.
    db_con = DBConnection(LOCAL_DB_URL)
    db_man = DBManager(Backups, db_con)
    db_man.truncate_table()
    db_man.add_data(data)
