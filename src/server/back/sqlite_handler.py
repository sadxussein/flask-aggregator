"""Database interactions module."""

import sqlite3
from .config import SQLITE_FOLDER
from .logger import Logger

class SQLiteHandler():
    """Insert/update/delete info in database."""
    def __init__(self, db_name=f"{SQLITE_FOLDER}/aggregator.db"):
        self.__db_name = db_name
        self.__logger = Logger()
        self.__conn = sqlite3.connect(self.__db_name)
        self.__create_tables()

    def __create_tables(self) -> None:
        """Create set of tables if they don't exist.
        
        Currenty tables created are: vms, hosts, clusters, storages, 
        data_centers.
        """
        # VMs table.
        cursor = self.__conn.cursor()
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS vms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid UUID UNIQUE,
                    name TEXT,
                    hostname TEXT,
                    state TEXT,
                    ip TEXT,
                    engine TEXT,
                    host TEXT,
                    cluster TEXT,
                    data_center TEXT,
                    was_migrated NUMERIC,
                    total_space REAL,
                    storage_domains TEXT,
                    href TEXT,
                    virtualization TEXT
                )
            """
        )
        # Hosts table.
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS hosts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid UUID UNIQUE,
                    name TEXT,
                    cluster TEXT,
                    data_center TEXT,
                    ip TEXT,
                    engine TEXT,
                    href TEXT,
                    virtualization TEXT
                )
            """
        )
        # Clusters table.
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS clusters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid UUID UNIQUE,
                    name TEXT,
                    description TEXT,
                    data_center TEXT,
                    engine TEXT,
                    href TEXT,
                    virtualization TEXT
                )
            """
        )
        # Storages table.
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS storages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid UUID UNIQUE,
                    name TEXT,
                    engine TEXT,
                    data_center TEXT,
                    available FLOAT,
                    used FLOAT,
                    committed FLOAT,
                    total FLOAT,
                    percent_left FLOAT,
                    overprovisioning FLOAT,
                    href TEXT,
                    virtualization TEXT
                )
            """
        )
        # Data centers table.
        cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS data_centers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid UUID UNIQUE,
                    name TEXT,
                    comment TEXT,
                    engine TEXT,
                    href TEXT,
                    virtualization TEXT
                )
            """
        )

    def insert_data(self, table: str, data: list) -> None:
        """Insert data into specific table.
        
        Args:
            table (str): Table name.
            data (list): Data to be inserted in form of list of dicts.
        """
        self.__logger.log_info(
            f"{self.__class__.__name__} - Updating table {table}."
        )
        cursor = self.__conn.cursor()
        for element in data:
            keys = ", ".join(element.keys())
            values = ", :".join(element.keys())
            update_clause = ", ".join(
                [
                    f"{key} = excluded.{key}" for key 
                    in element.keys() if key != "UUID"
                ]
            )
            cursor.execute(
                f"INSERT INTO {table} ({keys}) VALUES (:{values})"
                f"ON CONFLICT(UUID) DO UPDATE SET {update_clause}",
                element
            )
            self.__conn.commit()

    def get_data(self, table: str, filters: dict=None) -> list:
        """Get data as dict from specific table.
        
        Args:
            table (str): Table name.
            filter (dict): Filter for query. If empty function returns
            all table entries, if not filter is applied to query.

        Returns:
            (list): List of dicts of all entities in the table.
        """
        # Setting up connection to return dicts.
        self.__conn.row_factory = sqlite3.Row
        cursor = self.__conn.cursor()
        query = f"SELECT * FROM {table}"
        query_conditions = []
        query_params = []
        # Getting info from target table.
        if filters:
            for k, v in filters.items():
                if v:
                    query_conditions.append(f"{k} LIKE ?")
                    query_params.append(f"%{v}%")
        if query_conditions:
            query += " WHERE " + " AND ".join(query_conditions)
        cursor.execute(query, query_params)
        rows_with_dict = cursor.fetchall()
        # Returning connection to default.
        self.__conn.row_factory = None
        return [dict(row) for row in rows_with_dict]
