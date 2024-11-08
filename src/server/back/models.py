"""Database models module."""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, UUID, create_engine
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class OvirtEntity():
    """Base class for every oVirt entity."""
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID, unique=True, nullable=False)
    name = Column(String)
    engine = Column(String)
    href = Column(String)
    virtualization = Column(String)

class Vm(Base, OvirtEntity):
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

class Host(Base, OvirtEntity):
    """oVirt host model class."""
    __tablename__ = "hosts"

    ip = Column(String)
    cluster = Column(String)
    data_center = Column(String)

class Cluster(Base, OvirtEntity):
    """oVirt cluster model class."""
    __tablename__ = "clusters"

    data_center = Column(String)
    description = Column(String)

class Storage(Base, OvirtEntity):
    """oVirt storage model class."""
    __tablename__ = "storages"

    data_center = Column(String)
    available = Column(Float)
    used = Column(Float)
    committed = Column(Float)
    total = Column(Float)
    percent_left = Column(Float)
    overprovisioning = Column(Float)

class DataCenter(Base, OvirtEntity):
    """oVirt data center model class."""
    __tablename__ = "data_centers"

    comment = Column(String)

def get_engine(db_url):
    """Return corresponding engine to database manager class."""
    return create_engine(db_url)
