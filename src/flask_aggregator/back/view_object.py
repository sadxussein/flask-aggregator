"""View objects with decorators."""

from abc import ABC, abstractmethod

from sqlalchemy import Row

from flask_aggregator.back.models import get_base

class ViewObject(ABC):
    """Abstract class for all view objects."""
    @abstractmethod
    def to_dict(self):
        """Every view object should be able to represent itself as dict/JSON.
        """

    @abstractmethod
    def get_obj_attrs(self):
        """Get object attributes as list."""

class ViewObjectFactory:
    """Simple factory to get view objects."""
    @staticmethod
    def create_obj(obj) -> ViewObject:
        """Return concrete view object."""
        if isinstance(obj, Row):
            return SQLTupleViewObject(obj)
        if issubclass(obj.__class__, get_base()):
            return SQLModelViewObject(obj)
        raise ValueError("Unknown object class instance.")

class SQLModelViewObject(ViewObject):
    """Concrete SQLAlchemy model (table) view object."""
    def __init__(self, model):
        # Copying source class attributes to this one.
        # This might be redundant, but I want to have some flexibility if
        # ViewObject class functionality will be extended. Working with class
        # attributes is more 'clean' (IMO).
        self.__cols = [f.name for f in model.__table__.columns]
        for col in self.__cols:
            setattr(self, col, getattr(model, col))

    def to_dict(self):
        return (
            dict(
                zip(
                    self.__cols, (
                        getattr(self, col) for col in self.__cols
                    )
                )
            )
        )

    def get_obj_attrs(self):
        return self.__cols

class SQLTupleViewObject(ViewObject):
    """Concrete SQLAlchemy tuple (query result) view object."""
    def __init__(self, row_obj):
        # Copying source class attributes to this one.
        # This might be redundant, but I want to have some flexibility if
        # ViewObject class functionality will be extended. Working with class
        # attributes is more 'clean' (IMO).
        self.__cols = list(row_obj._fields)
        for col in self.__cols:
            setattr(self, col, getattr(row_obj, col))

    def to_dict(self):
        return (
            dict(
                zip(
                    self.__cols, (
                        getattr(self, col) for col in self.__cols
                    )
                )
            )
        )

    def get_obj_attrs(self):
        return self.__cols
