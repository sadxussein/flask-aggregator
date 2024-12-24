"""Elma interactions module."""

import json
import pandas
import requests

from flask_aggregator.back.dbmanager import DBManager
from flask_aggregator.back.models import ElmaVmAccessDoc
from flask_aggregator.back.logger import Logger
from flask_aggregator.config import Config

class ElmaHelper():
    """Class for Elma interactions."""
    URL_AUTH = "https://elma.rncb.ru/API/REST/Authorization/LoginWith"
    URL_QUERY = "https://elma.rncb.ru/API/REST/Entity/QueryTree"

    def __init__(self, logger=Logger(), dbmanager=DBManager()):
        self.__dbmanager = dbmanager
        self.__logger = logger

    def __get_auth_token(self) -> str:
        """Get auth token.
        
        Returns:
            str: Auth token.
        """
        url = self.URL_AUTH
        querystring = {"username": "RedVirt"}
        payload = Config.get_elma_pass()
        headers = {
            "applicationtoken": f"{Config.get_elma_token()}",
            "content-type": "application/json"
        }
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            params=querystring,
            timeout=30
        )
        return response.json()["AuthToken"]

    def __get_data_from_query_tree(self, query_dict: dict) -> json:
        """Get data from QueryTree by url with parameters.
        
        Args:
            query_dict (dict): Dict with filter parameters. Example:

        Returns:
            json: data as JSON.
        """
        url = self.URL_QUERY
        authtoken = self.__get_auth_token()
        headers = {
            "authtoken": authtoken,
            "webdata-version": "2.0"
        }
        response = requests.get(
            url,
            headers=headers,
            params=query_dict,
            timeout=30
        )
        response.encoding = "utf-8-sig"
        return response.json()

    def __prepare_vm_access_doc_data(self, data: json) -> list:
        """Transform data from JSON view to list of ElmaVmAccessDoc."""
        result = []
        for el in data:
            result.append(
                ElmaVmAccessDoc(
                    doc_id=el["Id"],
                    name=el["VmHostName"],
                    dns=el["HostName"],
                    backup=bool(el["Backup"])
                )
            )
        return result

    def import_vm_access_doc(self) -> None:
        """Importing VM document data.
        
        Main purpose of this function is to take data from Elma and paste it
        into `aggregator_db` table `elma_vm_access_doc`. This is done to have
        an understanding about which VM's had `Backup` tag when they were 
        ordered. 
        """
        data = self.__get_data_from_query_tree(
            {
                "type": ElmaEntity.VM_ACCESS_DOC,
                "q": "Backup = TRUE",
                "select": ["HostName", "VmHostName", "Backup"]
            }
        )
        data = self.__prepare_vm_access_doc_data(data)
        self.__dbmanager.add_data(data)

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

class ElmaEntity():
    """ID <-> readable name."""
    VM = "1d3f3776-30b7-4e73-b6eb-8a016322a471"
    VM_ACCESS_DOC = "c950e971-1fc8-496e-8b06-08de11b5a75d"
    VM_ACCESS_LIST_DOC = "02cea47f-d557-4290-81ba-3e67ca7506f7"
    DOCUMENT = "77a266e2-e8df-41ab-82ee-8fd93db77eec"
