"""Attempt to make full-scale controller (MVC pattern)."""

from abc import ABC, abstractmethod

import pandas as pd

import flask_aggregator.config as cfg
from flask_aggregator.back.dbmanager import DBManager
from flask_aggregator.back.models import Storage, Backups
from flask_aggregator.back.ovirt_helper import OvirtHelper

from flask_aggregator.back.db import DBConnection, DBRepositoryFactory


class Controller(ABC):
    """Abstract controller method.
    
    Acts as a mediator between 'model' and 'view'.
    Provides standart interface for client to use data from backend, whatever
    it is.
    """
    def __init__(self, source, target):
        self._source = source
        self._target = target

    @abstractmethod
    def get_data(self):
        """Get data from source."""

    @abstractmethod
    def set_data(self):
        """Set data in target."""

class DBController():
    """Controller for database set/get interactions."""
    def __init__(self, repo_name: str):
        db_con = DBConnection(cfg.DevelopmentConfig.DB_URL)
        repo_factory = DBRepositoryFactory()
        repo_factory.set_connection(db_con)
        repo = repo_factory.make_repo(repo_name)
        self.__n, self.__data = repo.build()

    def get_data(self):
        """Get result from database repository (table/view)."""
        return self.__data

    def get_item_count(self):
        """Get item count from current repo query."""
        return self.__n

    def set_data(self):
        """Set data in the database (upsert)."""

class Object():
    pass



# Transformers.
class Adapter(ABC):
    """Adapter class/interface for any view."""
    @abstractmethod
    def adapt(self, data: list) -> None:
        """
        Transform data by certain algorythm.

        Args:
            data (list): JSON-formatted data.

        Data is transformed in place, meaning that adapt fuction returns
        nothing.
        
        Data should be used in JSON format - e.g.
        ```
        [
            {
                "field1": data1,
                "field2": data2
            },
            {
                "field1": data3,
                "field2": data4
            }
        ]
        ```
        """

class GBAdapter(Adapter):
    """Transforming bytes to gigabytes.
    
    Only valid for `storage` table so far.
    """
    def adapt(self, data: list) -> None:
        if isinstance(data[0], Storage):
            for i, el in enumerate(data):
                d = el.__dict__.copy()
                d.pop("_sa_instance_state")
                d["available"] = d["available"] / 1024**3
                d["used"] = d["used"] / 1024**3
                d["total"] = d["total"] / 1024**3
                d["committed"] = d["committed"] / 1024**3
                data[i] = el.__class__(**d)
        else:
            raise ValueError(
                f"Data invalid. Class {self.__class__.__name__} accepts only "
                "'storage' table."
            )


class DBTableToDictAdapter(Adapter):
    """Translate data from ORM to dict type."""
    def adapt(self, data: list) -> None:
        for i, el in enumerate(data):
            data[i] = el.as_dict


class BackupTypeAdapter(Adapter):
    """Change long source_key url to short 'tape'/'disk'."""
    def adapt(self, data: list) -> None:
        for i, el in enumerate(data):
            new_el = Object()
            for k in Backups.__table__.columns:
                print(k)
                if k == "source_key":
                    setattr(
                        new_el,
                        k,
                        "tape" if "POOL" in el.source_key else "disk"
                    )
                else:
                    setattr(
                        new_el,
                        k,
                        getattr(el, k)
                    )
            data[i] = new_el

class TestAdapter(Adapter):
    """Transforming list of dicts (JSON) to pandas dataframe."""
    def adapt(self, data) -> pd.DataFrame:
        return pd.DataFrame(data)


# class Controller(ABC):
#     """Abstract controller class."""
#     def __init__(self):
#         self._adapters = []
#         # self._view = None
#         self._model = None

#     def add_adapter(self, adapter: Adapter):
#         """Add adapter which can change data passed to view."""
#         self._adapters.append(adapter)

#     def set_model(self, model: any):
#         """Set model for controller from which controller will take data."""
#         self._model = model

#     @abstractmethod
#     def get_data(self):
#         """Get data from model source."""

#     @abstractmethod
#     def update_data(self):
#         """Update data in model."""


# class DBController(Controller):
#     """Concrete database controller."""
#     def get_data(self):
#         d = self._model.data
#         if self._adapters:
#             for a in self._adapters:
#                 a.adapt(d)
#         return d

#     def update_data(self):
#         pass
