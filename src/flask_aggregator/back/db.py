"""Test module for database interactions architecture."""

from abc import ABC, abstractmethod

from sqlalchemy import create_engine, func, asc, desc
from sqlalchemy.orm import scoped_session, sessionmaker

from flask_aggregator.back.models import (
    Backups,
    Vm,
    Host,
    Storage,
    Cluster,
    DataCenter,
    ElmaVM,
    ElmaVmAccessDoc,
)

class DBConnection:
    """Handles database connections via SQLAlchemy."""

    def __init__(self, db_url: str):
        self.__engine = create_engine(db_url)
        session_factory = sessionmaker(bind=self.__engine)
        self.__ss = scoped_session(session_factory)

    def get_engine(self):
        """Get engine for external client."""
        return self.__engine

    def get_scoped_session(self):
        """Simply return scoped session for external client."""
        return self.__ss()

    def close_session(self):
        """Close current session with DB."""
        self.__ss.remove()


class DBManager(ABC):
    """Abstract class for managing table/view creation."""    
    # @abstractmethod
    # def upsert_data(
    #     self, data: list, index_elements: list, included_elements: list
    # ) -> None:
    #     """Upsert data to tables based on their type.

    #     Args:
    #         data (list): Data, either list of dicts (with all fields of model)
    #             or list of model elements (i.e. derived from Base ORM class).
    #         index_elements (list): List or strings, representing fields
    #             (columns), which have to be excluded from ON CONFLICT clause
    #             (to the right side of the clausee).
    #         included_elements (list): List of strings, representing elements
    #             to be excluded from the right side of DO UPDATE SET (these
    #             elements will not be updated on conflict).

    #     Returns:
    #         None

    #     Examples:
    #         The result query will be as such:
    #             ```
    #             INSERT INTO elma_vm_access_doc (id, doc_id, name, dns,
    #             backup) VALUES (%(id)s, %(doc_id)s, %(name)s, %(dns)s,
    #             %(backup)s) ON CONFLICT (uuid) DO UPDATE SET doc_id =
    #             excluded.doc_id, name = excluded.name, dns =
    #             excluded.dns, backup = excluded.backup
    #             ```
    #     """

    # @abstractmethod
    # def get_raw_data(self):
    #     """Return all data rows from query."""

    # @abstractmethod
    # def get_filtered_data(self) -> list:
    #     """Return filtered data from table."""

    # @abstractmethod
    # def get_paginated_data(self) -> list:
    #     """Return paginated and filtered data from table."""

    # @abstractmethod
    # def truncate(self) -> None:
    #     """Drop all rows from table."""


class DBFilter:
    """Database-specific filters."""

    def __init__(
        self,
        filters: dict = None,
        sort_by: str = None,
        sort_order: str = None,
        page: int = None,
        per_page: int = None,
    ):
        self.filters = filters
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.page = page
        self.per_page = per_page


class DBRepository(ABC):
    """Abstract class for different variants of database interactions.

    Driver may vary.
    """

    def __init__(self, conn: DBConnection):
        self._conn = conn
        self._s = self._conn.get_scoped_session()
        self._filter = DBFilter()
        self._col_order = []
        self._filter_fields = []
        self._query = None

    @property
    def data(self) -> list:
        """Return data as list."""
        if self._query is None:
            raise ValueError("Query is empty!")
        if self._query.all() is None:
            raise ValueError("Data is empty!")
        return self._query.all()

    @property
    def item_count(self) -> int:
        """Return """
        if self._query is None:
            raise ValueError("Query is empty!")
        if self._query.all() is None:
            raise ValueError("Data is empty!")
        return self._query.count()

    @property
    def col_order(self):
        """Get column order for repository."""
        return self._col_order

    @property
    def filter_fields(self):
        """Get column names by which repo can be filtered."""
        return self._filter_fields

    def add_filter(
        self,
        filters: dict = None,
        sort_by: str = None,
        sort_order: str = None,
        page: int = None,
        per_page: int = None,
    ):
        """Make filter for the repository (table query)."""
        self._filter = DBFilter(filters, sort_by, sort_order, page, per_page)

    def set_col_order(self, lst: list[str] = None):
        """Set column order for repository."""
        self._col_order = lst

    def set_filter_fields(self, lst: list[str] = None):
        """Set filter fields (columns) for repository."""
        self._filter_fields = lst

    def build(self) -> tuple[list, int]:
        """All-in-one function to make a document."""
        self.set_base_query()
        self.set_filter()
        n = self._query.count()
        self.set_order()
        self.set_pagination()
        return self._query.all(), n

    @abstractmethod
    def set_base_query(self):
        """Base query for current database interaction (repository)."""

    @abstractmethod
    def set_filter(self):
        """Set filters, based on which SQL statement will be created."""

    @abstractmethod
    def set_order(self):
        """Set asc/desc order of items.

        Args:
            col_name (str): Name of the column in the table.
            order (str): Will be sorted in ascending if order is `asc`,
                descending otherwise.
        """

    @abstractmethod
    def set_pagination(self):
        """Set items per page and current page.

        Args:
            per_page (int): Item count to be shows per page.
            page (int): Current page index.
        """


class LatestBackupRepository(DBRepository):
    """Get latest (by time) backups of VMs to disk-based archive locations.

    Tables involved: `backups`.

    First we make filtered query in order to drop all `POOL`-like entries
    (ie taped backups). Then grouping them by latest data creation.
    """
    def __init__(self, conn):
        super().__init__(conn)
        self._col_order = ["uuid", "name", "size", "source_key", "type"]
        self._filter_fields = ["name", "source_key", "type"]

    def set_base_query(self):
        filtered_query = self._s.query(Backups).filter(
            Backups.source_key.not_like("%POOL%")
        )
        subquery = (
            filtered_query.with_entities(
                Backups.name, func.max(Backups.created).label("latest_created")
            )
            .group_by(Backups.name)
            .subquery()
        )
        self._query = self._s.query(Backups).join(
            subquery,
            (Backups.name == subquery.c.name)
            & (Backups.created == subquery.c.latest_created),
        )
        return self

    def set_filter(self):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply filter to empty query."
            )
        if self._filter and self._filter.filters:
            for k, v in self._filter.filters.items():
                if v != "" and v is not None:
                    col = getattr(Backups, k, None)
                    if col is not None:
                        # TODO: need to think about strict and non-strict search
                        self._query = self._query.filter(col.like(f"%{v}%"))
        return self

    def set_order(self):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply order_by to empty query."
            )
        if self._filter and self._filter.sort_by and self._filter.sort_order:
            sb = self._filter.sort_by
            so = self._filter.sort_order
            col = getattr(Backups, sb, None)
            if col is not None:
                if so == "asc":
                    self._query.order_by(asc(col))
                else:
                    self._query.order_by(desc(col))
        return self

    def set_pagination(self):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply offset and limit to empty "
                "query."
            )
        if self._filter and self._filter.page and self._filter.per_page:
            p = self._filter.page
            pp = self._filter.per_page
            self._query = self._query.offset((p - 1) * pp).limit(pp)
        return self


class LatestBackupOvirtRepository(DBRepository):
    """Join between backup and redvirt repository.

    Showing only those VMs that are backed up and are present in oVirt.
    """

    def __init__(self, conn):
        super().__init__(conn)
        self._col_order = ["uuid", "name", "engine"]
        self._filter_fields = ["name", "engine"]

    def set_base_query(self):
        subquery = (
            self._s.query(
                Backups.name, func.max(Backups.created).label("latest_created")
            )
            .group_by(Backups.name)
            .subquery()
        )
        self._query = (
            self._s.query(
                Vm.id.label("id"),
                Vm.uuid.label("uuid"),
                Vm.name.label("name"),
                Vm.engine.label("engine"),
            )
            .join(ElmaVmAccessDoc, Vm.name == ElmaVmAccessDoc.name)
            .join(subquery, ElmaVmAccessDoc.name == subquery.c.name)
            .filter(ElmaVmAccessDoc.backup == True)
        )

    def set_filter(self):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply filter to empty query."
            )
        if self._filter and self._filter.filters:
            for k, v in self._filter.filters.items():
                if v != "" and v is not None:
                    col = next((c for c in self._col_order if c == k), None)
                    col = getattr(Vm, col, None)
                    if col is not None:
                        # TODO: need to think about strict and non-strict search
                        self._query = self._query.filter(col.like(f"%{v}%"))
        return self

    def set_order(self):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply order_by to empty query."
            )
        if self._filter and self._filter.sort_by and self._filter.sort_order:
            sb = self._filter.sort_by
            so = self._filter.sort_order
            col = next((c for c in self._col_order if c == sb), None)
            if col is not None:
                if so == "asc":
                    self._query = self._query.order_by(asc(col))
                else:
                    self._query = self._query.order_by(desc(col))
        return self

    def set_pagination(self):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply offset and limit to empty "
                "query."
            )
        if self._filter and self._filter.page and self._filter.per_page:
            p = self._filter.page
            pp = self._filter.per_page
            self._query = self._query.offset((p - 1) * pp).limit(pp)
        return self


class VmOvirtRepository(DBRepository):
    """Vm list from database."""
    def set_base_query(self):
        self._query = self._s.query(Vm)

    def set_filter(self):
        pass

    def set_order(self):
        pass

    def set_pagination(self):
        pass

class DBBasicRepository(DBRepository):
    """Interactions with base SQLAlchemy models."""
    def __init__(self, conn):
        super().__init__(conn)
        self.__m = None

    def set_model(self, model: any):
        """Set base model from SQLAlchemy."""
        self.__m = model

    def set_base_query(self):
        self._query = self._s.query(self.__m)
        return self

    def set_filter(self):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply filter to empty query."
            )
        if self._filter and self._filter.filters:
            for k, v in self._filter.filters.items():
                if v != "" and v is not None:
                    col = getattr(self.__m, k, None)
                    if col is not None:
                        # TODO: need to think about strict and non-strict search
                        self._query = self._query.filter(col.like(f"%{v}%"))
        return self

    def set_order(self):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply order_by to empty query."
            )
        if self._filter and self._filter.sort_by and self._filter.sort_order:
            sb = self._filter.sort_by
            so = self._filter.sort_order
            col = getattr(self.__m, sb, None)
            if col is not None:
                if so == "asc":
                    self._query.order_by(asc(col))
                else:
                    self._query.order_by(desc(col))
        return self

    def set_pagination(self):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply offset and limit to empty "
                "query."
            )
        if self._filter and self._filter.page and self._filter.per_page:
            p = self._filter.page
            pp = self._filter.per_page
            self._query = self._query.offset((p - 1) * pp).limit(pp)
        return self

class DBRepositoryFactory:
    """Factory for creating various database interactions endpoints."""

    def __init__(self):
        self.__db_conn = None

    def set_connection(self, conn: DBConnection):
        """Set DB connection for factory."""
        self.__db_conn = conn

    def make_repo(self, repo_name: str) -> DBRepository:
        """_summary_

        Args:
            repo_name (str): Repository name.

        Returns:
            DBRepository: Database repository (table/view), which can get
                data and 'beautify' it.
        """
        if repo_name == "LatestBackup":
            repo = LatestBackupRepository(self.__db_conn)
            repo.set_col_order(["uuid", "name", "size", "source_key", "type"])
            repo.set_filter_fields(["name", "source_key", "type"])
            return repo
        if repo_name == "LatestBackupOvirt":
            repo = LatestBackupOvirtRepository(self.__db_conn)
            repo.set_col_order(["uuid", "name", "engine"])
            repo.set_filter_fields(["name", "engine"])
            return repo
        if repo_name == "VmOvirt":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(Vm)
            repo.set_col_order(["uuid", "name", "engine", "ip"])
            repo.set_filter_fields(["uuid", "name", "engine", "ip"])
            return repo
        if repo_name == "HostOvirt":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(Host)
            repo.set_col_order(["uuid", "name", "engine", "ip"])
            repo.set_filter_fields(["uuid", "name", "engine", "ip"])
            return repo
        if repo_name == "ClusterOvirt":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(Cluster)
            repo.set_col_order(["uuid", "name", "engine"])
            repo.set_filter_fields(["uuid", "name", "engine"])
            return repo
        if repo_name == "DataCenterOvirt":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(DataCenter)
            repo.set_col_order(["uuid", "name", "engine"])
            repo.set_filter_fields(["uuid", "name", "engine"])
            return repo
        if repo_name == "StorageOvirt":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(Storage)
            repo.set_col_order(["uuid", "name", "engine"])
            repo.set_filter_fields(["uuid", "name", "engine"])
            return repo
        if repo_name == "Backups":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(Backups)
            repo.set_col_order(
                ["name", "created", "type", "size", "source_key"]
            )
            repo.set_filter_fields(["name", "type"])
            return repo
        if repo_name == "ElmaVm":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(ElmaVM)
            repo.set_col_order(["id", "name", "administrators"])
            repo.set_filter_fields(["id", "name"])
            return repo
        if repo_name == "ElmaVmAccessDoc":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(ElmaVmAccessDoc)
            repo.set_col_order(["id", "doc_id", "name", "dns", "backup"])
            repo.set_filter_fields(["id", "doc_id", "name", "dns", "backup"])
            return repo
        raise ValueError("'repo_name' is invalid.")
