"""View objects with decorators."""

from collections import OrderedDict
from abc import ABC, abstractmethod

from sqlalchemy import Row

from flask_aggregator.back.models import get_base

def convert_bytes(col_name, unit="GB"):
    """Recalculating bytes for convenience. Only dicts."""
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}

    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, dict) and col_name in result:
                b = result[col_name]
                if unit in units:
                    result[col_name] = b / units[unit]
                else:
                    raise ValueError(
                        "Unknown unit! Allowed: B, KB, MB, GB, TB."
                    )
            return result
        return wrapper
    return decorator

def convert_backup_type(col_name):
    """So far, viable only for Backups table (column 'source_key').

    And converting only dicts."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if isinstance(result, dict) and col_name in result:
                result[col_name] = (
                    "tape" if "POOL" in result[col_name] else "disk"
                )
            return result
        return wrapper
    return decorator


class ViewObject(ABC):
    """Abstract class for all view objects."""
    @abstractmethod
    def to_dict(self):
        """Every view object should be able to represent itself as dict/JSON.
        """

    @abstractmethod
    def get_obj_attrs(self):
        """Get object attributes as list."""

    @abstractmethod
    def set_obj_attrs(self, lst: list[str]):
        """Set object attributes from list."""

class ViewObjectFactory:
    """Simple factory to get view objects."""
    @staticmethod
    def create_obj(obj, cols) -> ViewObject:
        """Return concrete view object."""
        if isinstance(obj, Row):
            return SQLTupleViewObject(obj, cols)
        if issubclass(obj.__class__, get_base()):
            return SQLModelViewObject(obj, cols)
        raise ValueError("Unknown object class instance.")

class SQLModelViewObject(ViewObject):
    """Concrete SQLAlchemy model (table) view object."""
    def __init__(self, model, cols):
        # Copying source class attributes to this one.
        # This might be redundant, but I want to have some flexibility if
        # ViewObject class functionality will be extended. Working with class
        # attributes is more 'clean' (IMO).
        self.__cols = cols
        for col in self.__cols:
            setattr(self, col, getattr(model, col))

    @convert_backup_type("source_key")
    @convert_bytes("total", "GB")
    @convert_bytes("available", "GB")
    def to_dict(self):
        return (
            OrderedDict(
                zip(
                    self.__cols, (
                        getattr(self, col) for col in self.__cols
                    )
                )
            )
        )

    def set_obj_attrs(self, lst: list[str]):
        self.__cols = lst

    def get_obj_attrs(self):
        return self.__cols

class SQLTupleViewObject(ViewObject):
    """Concrete SQLAlchemy tuple (query result) view object."""
    def __init__(self, row_obj, cols):
        # Copying source class attributes to this one.
        # This might be redundant, but I want to have some flexibility if
        # ViewObject class functionality will be extended. Working with class
        # attributes is more 'clean' (IMO).
        self.__cols = cols
        for col in self.__cols:
            setattr(self, col, getattr(row_obj, col))

    @convert_backup_type("source_key")
    @convert_bytes("total", "GB")
    @convert_bytes("available", "GB")
    def to_dict(self):
        return (
            OrderedDict(
                zip(
                    self.__cols, (
                        getattr(self, col) for col in self.__cols
                    )
                )
            )
        )

    def set_obj_attrs(self, lst: list[str]):
        self.__cols = lst

    def get_obj_attrs(self):
        return self.__cols
