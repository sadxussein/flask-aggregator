"""Database interactions with Cyberbackup."""

import os

from flask_aggregator.back.models import Backups, CyberbackupServers
from flask_aggregator.back.logger import Logger
from flask_aggregator.back.db import DBConnection, DBManager, DBROManager
from flask_aggregator.config import (
    Config, DevelopmentConfig, ProductionConfig
)

# class CyberbackupHelper():
#     """Cyberbackup helper class."""
#     def __init__(self, dpc: str, logger: Logger=Logger()):
#         self.__logger = logger
#         self.__dpc = dpc
#         db_password = None
#         if dpc == "e15":
#             db_password = os.getenv("CB_DB_PASS_E15")
#         elif dpc in ["n32", "k45"]:
#             db_password = os.getenv("CB_DB_PASS_N32_K45")
#         if db_password is not None:
#             self.__database = DBManager(
#                 db_url=f"postgresql+psycopg2://"
#                 f"{Config.CYBERBACKUP_DB_USER}:"
#                 f"{db_password}@"
#                 f"{Config.CYBERBACKUP_DB_ADDRESSES[dpc]}:"
#                 f"{Config.CYBERBACKUP_DB_PORT}/"
#                 f"{Config.CYBERBACKUP_DB_NAME}"
#             )
#         else:
#             raise ValueError("Failed to get CB password from ENV.")

#     def add_data_as_dict(self) -> None:
#         """Get all data from CB table."""
#         raw_data = self.__database.run_simple_query(
#             "select DISTINCT ON (a.resource_name, b.created_time) "
#             "a.resource_name, b.resource_ids, to_timestamp(b.created) "
#             "as start_time, to_timestamp(b.created_time) as end_time, "
#             "b.size, b.source_key, b.disks, b.type FROM	backups b LEFT JOIN "
#             "archives a ON b.resource_ids like '%'||a.resource_id||'%'"
#         )

#         data = []
#         if raw_data:
#             for row in raw_data:
#                 namespace = uuid.UUID("12345678-1234-1234-1234-123456789123")
#                 upstert_uuid = uuid.uuid5(
#                     namespace, f"{row[0]}-{row[2]}-{row[3]}"
#                 )
#                 db_el = {
#                     "name": row[0],
#                     "uuid": upstert_uuid,
#                     "backup_server": self.__dpc,
#                     "resource_ids": row[1],
#                     "created": row[2],
#                     "created_time": row[3],
#                     "size": row[4],
#                     "source_key": row[5],
#                     "disks": row[6],
#                     "type": row[7]
#                 }
#                 data.append(db_el)
#             aggregator_db = DBManager()
#             aggregator_db.upsert_data(Backups, data, ["uuid"], ["id", "uuid"])
#             aggregator_db.close()
#         else:
#             self.__logger.log_error("No data was collected.")


def set_cb_servers_data():
    """Upsert data in 'cyberbackup_servers' local table."""
    dbm = DBManager(
        CyberbackupServers,
        DBConnection(
            DevelopmentConfig.DB_URL
            if os.getenv("FA_ENV") == "dev" else
            ProductionConfig.DB_URL
        )
    )
    dbm.upsert_data(Config.CYBERBACKUP, ["name"], ["id"])


class CBHelper:
    """Cyberbackup helper class."""
    def __init__(self, db_url: str):
        self.__dbman = DBROManager(DBConnection(
            db_url
        ))

    def get_latest_backups(self):
        """Get data from 'backups' remote table."""
        return self.__dbman.get_all_data(
            "select DISTINCT ON (a.resource_name, b.created_time) "
            "a.resource_name, b.resource_ids, to_timestamp(b.created) "
            "as start_time, to_timestamp(b.created_time) as end_time, "
            "b.size, b.source_key, b.disks, b.type FROM	backups b LEFT JOIN "
            "archives a ON b.resource_ids like '%'||a.resource_id||'%'"
        )

    def get_all_data(self, table_name):
        """Get all rows from selected table."""
        return self.__dbman.get_all_data(
            f"select * from {table_name};"
        )
