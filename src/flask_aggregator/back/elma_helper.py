"""Elma interactions module."""

import pandas

from flask_aggregator.back.dbmanager import DBManager
from flask_aggregator.back.logger import Logger

class ElmaHelper():
    """Class for Elma interactions."""
    def __init__(self, logger=Logger(), dbmanager=DBManager()):
        self.__dbmanager = dbmanager
        self.__logger = logger

    def import_vm_list(self, table: any, file_path: str) -> None:
        """Importing file into database.
        
        Args:
            file (str): Path to file to be imported.

        Opening excel file, reading its with pandas. Checking its validity
        and importing into DB.
        """
        # If all fields are correct for certain table.
        # TODO: test checking if file exists.
        # TODO: test checking file validity.
        try:
            dataframe = pandas.read_excel(file_path)
            if (
                isinstance(dataframe, pandas.DataFrame)
                and not dataframe.empty
                and (
                    tuple(dataframe.columns)
                    == tuple(table.elma_field_names().values())
                )
            ):
                self.__logger.log_debug(
                    f"[{self.__class__.__name__}] "
                    f"Parsing file {file_path}."
                )
                dataframe.columns = list(table.elma_field_names().keys())
                dataframe.to_sql(
                    name=table.__tablename__,
                    con=self.__dbmanager.engine,
                    if_exists="replace",
                    index_label="id"
                )
            else:
                self.__logger.log_error(
                    f"[{self.__class__.__name__}] File either empty or has "
                    f"bad fields. Should be like: {table.elma_field_names()}"
                )
        except FileNotFoundError as e:
            self.__logger.log_error(
                f"[{self.__class__.__name__}] {e}."
            )
