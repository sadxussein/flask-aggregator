"""Attempt to make full-scale controller (MVC pattern)."""

from abc import ABC, abstractmethod

import pandas as pd

from flask_aggregator.config import Config as cfg
from flask_aggregator.back.dbmanager import DBManager
from flask_aggregator.back.models import Storage, Backups
from flask_aggregator.back.ovirt_helper import OvirtHelper


class ControllerInterface(ABC):
    """Abstract class/interface for all controllers."""
    @property
    @abstractmethod
    def data(self) -> any:
        """Controller always holds some data to present for view."""

    @property
    @abstractmethod
    def item_count(self) -> int:
        """Since this controller operates only with table-like entities it
        always returns item count (row count).
        """

    @abstractmethod
    def get_filters(self) -> None:
        """Set filters to view."""

    @abstractmethod
    def get_columns(self) -> None:
        """Set columns in order set in model."""


class DBController(ControllerInterface):
    """MVC Controller class for view-database interactions.
    
    Concrete class for database.
    """
    def __init__(self, table_name: str):
        super().__init__()
        self.__dbmanager = DBManager()
        self.__table = cfg.DB_MODELS[table_name]
        self.__data = self.__dbmanager.get_data(self.__table)
        self.__item_count = self.__dbmanager.get_item_count(self.__table)

    @property
    def data(self) -> any:
        return self.__data

    @property
    def item_count(self) -> int:
        return self.__item_count

    def get_taped_vms(self, model: any, **kwargs: any) -> list:
        self.__item_count, self.__data = (
            self.__dbmanager.get_taped_vms(model, **kwargs)
        )

    def get_old_backups(self, model: any, **kwargs: any) -> list:
        self.__item_count, self.__data = (
            self.__dbmanager.get_old_backups(model, **kwargs)
        )

    def get_filters(self) -> list:
        return self.__dbmanager.get_model_filters(self.__table)

    def get_columns(self) -> list:
        return self.__dbmanager.get_model_columns(self.__table)

class OvirtController(ControllerInterface):
    """MVC Controller class for oVirt interactions."""
    def __init__(self, dpc_list: list):
        """Always should have `dpc_list` parameter, otherwise no meaning."""
        self.__ovirt_helper = OvirtHelper(dpc_list=dpc_list)
        self.__data = None
        self.__item_count = None

    @property
    def data(self) -> any:
        return self.__data

    @property
    def item_count(self) -> int:
        return self.__item_count

    def get_filters(self):
        pass

    def get_columns(self):
        pass

    def get_user_vm_list(self) -> None:
        self.__ovirt_helper.connect_to_virtualization()
        self.__data = self.__ovirt_helper.get_user_vm_list()
        self.__item_count = len(self.__data)
        self.__ovirt_helper.disconnect_from_virtualization()

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

class Object():
    pass


class BackupTypeAdapter(Adapter):
    """Change long source_key url to short 'tape'/'disk'."""
    def adapt(self, data: list) -> None:
        for i, el in enumerate(data):
            new_el = Object()
            for k in el._mapping.keys():
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


# Views.
class DataView(ABC):
    """View class."""
    def __init__(self, transformers: list):
        self.__tfs = transformers

    @abstractmethod
    def update_view(self, data):
        """Update view for data."""

    @abstractmethod
    def _render_view(self, data):
        """Render view for external use."""

class StorageView(DataView):
    def __init__(self, transformers: list):
        self.__tfs = transformers

    def update_view(self, data):
        for tf in self.__tfs:
            tf.adapt(data)
        return self._render_view(data)

    def _render_view(self, data):
        return data

class BackupsView(DataView):
    def __init__(self, transformers: list):
        self.__tfs = transformers

    def update_view(self, data):
        for tf in self.__tfs:
            tf.adapt(data)
        return self._render_view(data)

    def _render_view(self, data):
        return data

class DataFrameView(DataView):
    def __init__(self, transformers: list):
        self.__tfs = transformers

    def update_view(self, data):
        for tf in self.__tfs:
            data = tf.adapt(data)
        return self._render_view(data)

    def _render_view(self, data):
        return data
