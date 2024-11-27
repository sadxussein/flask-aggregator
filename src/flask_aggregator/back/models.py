"""Database models module."""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, UUID, create_engine
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class OvirtEntity(Base):
    """Base class for every oVirt entity."""
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID, unique=True, nullable=False)
    name = Column(String)
    engine = Column(String)
    href = Column(String)
    virtualization = Column(String)

    @property
    def as_dict(self):
        """Return dict from model structure."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @staticmethod
    def get_columns_order():
        """Simply get starting order of columns of base class."""
        return ["uuid", "name", "engine", "href", "virtualization"]

    @staticmethod
    def get_filters():
        """Default set of filters."""
        return ["name", "engine", "virtualization"]

class Vm(OvirtEntity):
    """oVirt VM model class."""
    __tablename__ = "vms"

    hostname = Column(String)
    state = Column(String)
    ip = Column(String)
    host = Column(String)
    state = Column(String)
    cluster = Column(String)
    data_center = Column(String)
    was_migrated = Column(Boolean)
    total_space = Column(Float)
    storage_domains = Column(String)

    @staticmethod
    def get_columns_order():
        """Get full order of columns."""
        return OvirtEntity.get_columns_order() + [
            "hostname", "state", "ip", "host", "state", "cluster",
            "data_center", "was_migrated", "total_space", "storage_domains"
        ]

    @staticmethod
    def get_filters():
        """Full set of filters."""
        return OvirtEntity.get_filters() + ["ip"]

class Host(OvirtEntity):
    """oVirt host model class."""
    __tablename__ = "hosts"

    ip = Column(String)
    cluster = Column(String)
    data_center = Column(String)

    @staticmethod
    def get_columns_order():
        """Get full order of columns."""
        return OvirtEntity.get_columns_order() + [
            "ip", "cluster", "data_center"
        ]

    @staticmethod
    def get_filters():
        """Full set of filters."""
        return OvirtEntity.get_filters() + ["ip"]

class Cluster(OvirtEntity):
    """oVirt cluster model class."""
    __tablename__ = "clusters"

    data_center = Column(String)
    comment = Column(String)
    description = Column(String)

    @staticmethod
    def get_columns_order():
        """Get full order of columns."""
        return OvirtEntity.get_columns_order() + [
            "data_center", "comment", "description"
        ]

class Storage(OvirtEntity):
    """oVirt storage model class."""
    __tablename__ = "storages"

    data_center = Column(String)
    available = Column(Float)
    used = Column(Float)
    committed = Column(Float)
    total = Column(Float)
    percent_left = Column(Float)
    overprovisioning = Column(Float)

    @staticmethod
    def get_columns_order():
        """Get full order of columns."""
        return OvirtEntity.get_columns_order() + [
            "data_center", "available", "used", "committed", "total",
            "percent_left", "overprovisioning"
        ]

class DataCenter(OvirtEntity):
    """oVirt data center model class."""
    __tablename__ = "data_centers"

    comment = Column(String)

    @staticmethod
    def get_columns_order():
        """Get full order of columns."""
        return OvirtEntity.get_columns_order() + [
            "comment"
        ]

def get_engine(db_url):
    """Return corresponding engine to database manager class."""
    return create_engine(db_url)
