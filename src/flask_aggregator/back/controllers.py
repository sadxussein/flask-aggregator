"""Attempt to make full-scale controller (MVC pattern)."""

from abc import ABC, abstractmethod

from flask_aggregator.config import Config as cfg
from flask_aggregator.back.dbmanager import DBManager
from flask_aggregator.back.models import Storage


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
    
    Concrete class for 
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

    def get_filters(self) -> list:
        return self.__dbmanager.get_model_filters(self.__table)

    def get_columns(self) -> list:
        return self.__dbmanager.get_model_columns(self.__table)


class DataTransformer(ABC):
    """Transformer class/interface for flask HTML view."""
    @abstractmethod
    def transform(self, data: any) -> None:
        """Transform data by certain algorythm."""


class GBTransformer(DataTransformer):
    """Transforming bytes to gigabytes.
    
    Only valid for `storage` table so far.
    """
    def transform(self, data) -> None:
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


class TestTransformer(DataTransformer):
    """Transforming bytes to gigabytes.
    
    Only valid for `storage` table so far.
    """
    def transform(self, data) -> list:
        if isinstance(data[0], Storage):
            result = []
            for el in data:
                f = el.__dict__.copy()
                result.append(
                    el.__class__(**f)
                )
        else:
            raise ValueError(
                f"Data invalid. Class {self.__class__.__name__} accepts only "
                "'storage' table."
            )


class DataView(ABC):
    """View class."""
    def __init__(self, transformers: list):
        self.__tfs = transformers

    def update_view(self, data):
        for tf in self.__tfs:
            tf.transform(data)
        return self._render_view(data)

    @abstractmethod
    def _render_view(self, data):
        """Render view for external use."""


class StorageView(DataView):
    def _render_view(self, data):
        return data


# class DefaultView(DataView):
#     pass
