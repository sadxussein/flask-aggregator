"""Database models module."""

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, UUID, DateTime, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

def get_base():
    """For external use."""
    return Base

class OvirtEntity(Base):
    """Base class for every oVirt entity."""
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID, unique=True, nullable=False)
    name = Column(String)
    engine = Column(String)
    href = Column(String)
    virtualization = Column(String)
    time_created = Column(
        DateTime,
        default=datetime.now(timezone(timedelta(hours=3))),
        onupdate=datetime.now(timezone(timedelta(hours=3)))
    )

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
            "hostname", "state", "ip", "host", "cluster",
            "data_center", "was_migrated", "total_space", "storage_domains"
        ]

    @staticmethod
    def get_filters():
        """Full set of filters."""
        return OvirtEntity.get_filters() + ["ip", "storage_domains"]

class Host(OvirtEntity):
    """oVirt host model class."""
    __tablename__ = "hosts"

    name = Column(String, unique=True, nullable=False)
    ip = Column(String)
    cluster = Column(String)
    data_center = Column(String)
    status = Column(String)

    @staticmethod
    def get_columns_order():
        """Get full order of columns."""
        return OvirtEntity.get_columns_order() + [
            "ip", "cluster", "data_center", "status"
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

    @hybrid_property
    def available_gb(self):
        return self.available / 1024**3

    @hybrid_property
    def used_gb(self):
        return self.used / 1024**3

    @hybrid_property
    def committed_gb(self):
        return self.committed / 1024**3

    @hybrid_property
    def total_gb(self):
        return self.total / 1024**3

    @staticmethod
    def get_columns_order():
        """Get full order of columns."""
        return OvirtEntity.get_columns_order() + [
            "data_center", "available", "used", "committed",
            "total", "percent_left", "overprovisioning"
        ]

    # @staticmethod
    # def get_html_columns_order():
    #     """Get full order of columns for HTML view."""
    #     return OvirtEntity.get_columns_order() + [
    #         "data_center", "available_gb", "used_gb", "committed_gb",
    #         "total_gb", "percent_left", "overprovisioning"
    #     ]

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

class Backups(Base):
    """Base class for Cyberbackup backups history."""
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID, unique=True, nullable=False)
    name = Column(String)
    backup_server = Column(String)
    resource_ids = Column(String)
    created = Column(DateTime)
    created_time = Column(DateTime)
    size = Column(String)
    source_key = Column(String)
    disks = Column(String)
    type = Column(String)

    @property
    def as_dict(self):
        """Return dict from model structure."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @staticmethod
    def get_columns_order():
        """Get full order of columns.""" 
        return [
            "name", "backup_server", "created", "size", "source_key", "type"
        ]

    @staticmethod
    def get_filters():
        """Full set of filters."""
        return ["name", "backup_server", "source_key", "type"]

class ElmaVM(Base):
    """Elma VM table."""
    __tablename__ = "elma_vms"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID, unique=True, nullable=False)
    name = Column(String)
    host = Column(String)
    ips = Column(String)
    environment = Column(String)
    administrators = Column(String)
    users = Column(String)
    info_system = Column(String)
    software = Column(String)
    should_be_backuped = Column(Boolean, nullable=False)
    is_deleted = Column(Boolean, nullable=False)

    @staticmethod
    def elma_field_names():
        """Set of fields for file validity check."""
        return {
            "uuid": "Уникальный код",
            "name": "Наименование",
            "host": "Хост",
            "ips": "Ip адреса",
            "environment": "Рабочее окружение",
            "administrators": "Администраторы ИС",
            "users": "Пользователи (функциональные группы)",
            "info_system": "Информационные системы",
            "software": "ПО",
            "should_be_backuped": "Резервное копирование",
            "is_deleted": "IsDeleted"
        }

    @property
    def as_dict(self):
        """Return dict from model structure."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @staticmethod
    def get_columns_order():
        """Get full order of columns.""" 
        return ["name", "environment", "should_be_backuped"]

    @staticmethod
    def get_filters():
        """Full set of filters."""
        return ["name", "environment", "should_be_backuped"]

class ElmaVmAccessDoc(Base):
    """Model for VM order document (VmAccessDoc).
    
    Service table - should not be printed for user view.
    """
    __tablename__ = "elma_vm_access_doc"
    # Field taken from Elma VmAccessDoc entity:
    #   1. VmHostName (name)
    #   2. HostName (dns)
    #   3. Backup
    #   4. Id (doc_id)
    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, unique=True)
    name = Column(String)
    dns = Column(String)
    backup = Column(Boolean)

class BackupsView():
    """Read-only view for VM's which should be backed up and are backed up."""
    id = None 
    uuid = None
    name = None
    engine = None

    def __init__(self, id_: int, uuid_: uuid, name: str, engine: str):
        self.id = id_
        self.uuid = uuid_
        self.name = name
        self.engine = engine

    @property
    def as_dict(self):
        """Return dict from model structure."""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "name": self.name,
            "engine": self.engine
        }

    @staticmethod
    def table_name():
        return "backups_view"

    @staticmethod
    def get_columns_order():
        """Simply get starting order of columns of base class."""
        return ["uuid", "name", "engine"]

    @staticmethod
    def get_filters():
        """Default set of filters."""
        return ["name", "engine"]

class CBBackupsView:
    """View for unique CB backups entries, based on latest entry."""
    @staticmethod
    def table_name():
        return "cb_backups_view"
    
class VmsToBeBackedUpView:
    """View for VMs which have to be backed up be ELMA and are present in RV."""    
    id = None
    uuid = None
    name = None
    engine = None

    def __init__(self, id_: int, uuid_: uuid, name: str, engine: str):
        self.id = id_
        self.uuid = uuid_
        self.name = name
        self.engine = engine

    @property
    def as_dict(self):
        """Return dict from model structure."""
        return {
            "id": self.id,
            "uuid": self.uuid,
            "name": self.name,
            "engine": self.engine
        }
    
    @property
    def as_line(self):
        """Return line from model structure."""
        return f"{self.id}\t{self.uuid}\t{self.name}\t{self.engine}"

    @staticmethod
    def table_name():
        return "vms_to_be_backed_up_view"

    @staticmethod
    def get_columns_order():
        """Simply get starting order of columns of base class."""
        return ["uuid", "name", "engine"]

    @staticmethod
    def get_filters():
        """Default set of filters."""
        return ["name", "engine"]

