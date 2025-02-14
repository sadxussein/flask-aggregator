"""Test module for database interactions architecture."""

from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import datetime, timedelta

from sqlalchemy import create_engine, func, asc, desc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import scoped_session, sessionmaker

from flask_aggregator.back.models import (
    get_base,
    Backups,
    Vm,
    Host,
    Storage,
    Cluster,
    DataCenter,
    ElmaVM,
    ElmaVmAccessDoc,
    OvirtEngine
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
    """Class for managing table/view creation."""
    def __init__(self, model: any, conn: DBConnection):
        self.__m = model
        self.__s = conn.get_scoped_session()

        # Make table (if it doesn't exist) via DeclarativeBase from 'models'
        # module.
        get_base().metadata.create_all(
            bind=conn.get_engine(),
            tables=[model.__table__]
        )

    def upsert_data(
        self, data: list, index_elements: list, included_elements: list
    ) -> None:
        """Upsert data to tables based on their type.

        Args:
            data (list): Data, either list of dicts (with all fields of
                model) or list of model elements (i.e. derived from Base ORM
                class).
            index_elements (list): List or strings, representing fields
                (columns), based on which `ON CONFLICT` clause in constructed.
                Basically its a list of columns which have to be checked for 
                conflict. If it changes - do update for other columns. In
                example its `(uuid)` after `ON CONFLICT` clause.
            included_elements (list): From this list of elements will be 
                created list of excluded ones for the right side of 
                `DO UPDATE SET`. Only for elements that have 'unique' 
                constraint. In example below they are not present, since these
                elements are to be excluded from all elements. In other words:
                (excluded_elements = all_elements - included_elements)

        Returns:
            None

        Examples:
            The result query will be as such:
                ```
                INSERT INTO elma_vm_access_doc (id, doc_id, name, dns,
                backup) VALUES (%(id)s, %(doc_id)s, %(name)s, %(dns)s,
                %(backup)s) ON CONFLICT (uuid) DO UPDATE SET doc_id =
                excluded.doc_id, name = excluded.name, dns =
                excluded.dns, backup = excluded.backup
                ```
        """
        # Postgres specific "upsert".
        stmt = insert(self.__m).values(data)
        dict_set = {
            column.name: getattr(stmt.excluded, column.name)
            for column in self.__m.__table__.columns
            if column.name not in included_elements
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=index_elements,
            set_=dict_set
        )
        self.__s.execute(stmt)
        self.__s.commit()
        self.__s.close()

    def truncate_table(self):
        """Drop all rows from current model."""
        self.__s.query(self.__m).delete()
        self.__s.commit()
        self.__s.close()

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
        self._filter_fields = [{}]
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
        """Return"""
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

    def set_filter_fields(self, lst: list[dict[str, str]] = None):
        """Set filter fields (columns) for repository.
        
        Base format for list:
            ```
            [
                {
                    "name": "field_1",
                    "type": "text"
                    "default_value":
                }
            ]
            ```
        """
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
                if v != "" and v is not None and k != "source_key":
                    col = getattr(Backups, k, None)
                    if col is not None:
                        # TODO: need to think about strict and non-strict search
                        self._query = self._query.filter(col.like(f"%{v}%"))
                if k == "show_backups" and v != "" and v is not None:
                    month_ago = datetime.now() - timedelta(days=30)
                    two_days_ago = datetime.now() - timedelta(days=2)
                    if v == "older":
                        self._query = (
                            self._query
                            .filter(Backups.created < two_days_ago)
                            .filter(Backups.created > month_ago)
                        )
                    elif v == "newer":
                        self._query = self._query.filter(
                            Backups.created >= two_days_ago
                        )
                if k == "source_key" and v != "" and v is not None:
                    if v == "disk":
                        self._query = (self._query.filter(
                                ~Backups.source_key.like("%POOL%")
                        ))
                    elif v == "tape":
                        self._query = (self._query.filter(
                                Backups.source_key.like("%POOL%")
                        ))
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


class ToBeBackedUpVmsRepository(DBRepository):
    """A join of VMs which have to be backed up by cyberbackup.
    
    Tables involved: 'backups', 'elma_vm_access_doc', 'vms'.
    """
    def set_base_query(self):
        backups_subq = (
            self._s.query(Backups.name)
            .group_by(Backups.name)
            .subquery()
        )
        elma_q = (
            self._s.query(
                Vm.id.label("id"),
                Vm.uuid.label("uuid"),
                Vm.name.label("name"),
                Vm.engine.label("engine"),
            )
            .join(ElmaVmAccessDoc, Vm.name == ElmaVmAccessDoc.name)
            .join(backups_subq, ElmaVmAccessDoc.name == backups_subq.c.name)
            .filter(ElmaVmAccessDoc.backup == True)
            .subquery()
        )
        self._query = (
            self._s.query(
                Vm.id,
                Vm.uuid,
                ElmaVmAccessDoc.name,
                Vm.engine
            )
            .outerjoin(
                elma_q,
                elma_q.c.name == ElmaVmAccessDoc.name
            )
            .outerjoin(
                Vm, Vm.name == ElmaVmAccessDoc.name
            )
            .filter(
                ElmaVmAccessDoc.backup == True,
                elma_q.c.name == None
            )
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
                    col = next((c for c in self._col_order if c == k), None)
                    if col is not None:
                        if col != "name":
                            col = getattr(Vm, col, None)
                        else:
                            col = getattr(ElmaVmAccessDoc, col, None)
                        # TODO: need to think about strict and non-strict search
                        self._query = self._query.filter(col.like(f"%{v}%"))
                    # If in the frontend the button is in "disabled" state.
                if k == "show_dbs" and not v:
                    self._query = self._query.filter(
                        ~ElmaVmAccessDoc.name.like("%db%")
                    )
                # If in the frontend the button is in "disabled" state.
                if k == "show_absent_in_ov" and not v:
                    self._query = self._query.filter(Vm.uuid != None)
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


class TapedOnlyVmsRepository(DBRepository):
    """Only for VMs that have been taped by Cyberbackup."""
    def set_base_query(self):
        filtered_query = self._s.query(Backups).filter(
            Backups.source_key.like("%POOL%")
        )
        subquery = (
            filtered_query
            .with_entities(
                Backups.name,
                func.max(Backups.created).label("latest_created")
            )
            .group_by(Backups.name)
        )
        subquery = subquery.subquery()
        self._query = (
            self._s.query(Backups)
            .join(
                subquery,
                (Backups.name == subquery.c.name)
                & (Backups.created == subquery.c.latest_created)
                & (Backups.source_key.like("%POOL%"))
            )
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
                    col = next((c for c in self._col_order if c == k), None)
                    if col is not None:
                        if col != "name":
                            col = getattr(Vm, col, None)
                        else:
                            col = getattr(ElmaVmAccessDoc, col, None)
                        # TODO: need to think about strict and non-strict search
                        self._query = self._query.filter(col.like(f"%{v}%"))

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
            raise ValueError("Query is 'None'. Can't apply filter to empty query.")
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
            raise ValueError("Query is 'None'. Can't apply order_by to empty query.")
        if self._filter and self._filter.sort_by and self._filter.sort_order:
            sb = self._filter.sort_by
            so = self._filter.sort_order
            col = getattr(self.__m, sb, None)
            if col is not None:
                if so == "asc":
                    self._query = self._query.order_by(asc(col))
                else:
                    self._query = self._query.order_by(desc(col))
        return self

    def set_pagination(self):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply offset and limit to empty " "query."
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
            repo.set_col_order(["name", "created", "size", "source_key", "type"])
            repo.set_filter_fields([
                {"name": "name", "type": "text", "default_value": ''},
                {"name": "type", "type": "option", "options":
                    {"":"all", "full": "full", "incremental": "incremental"}
                },
                {"name": "source_key", "type": "option", "options":
                    {"":"all", "disk": "disk", "tape": "tape"}
                },
                {"name": "show_backups", "type": "option", "options": {
                    "":"all",
                    "older": "older than 2 days (<)",
                    "newer": "newer than 2 days (>=)"
                }},
            ])
            return repo
        if repo_name == "LatestBackupOvirt":
            repo = LatestBackupOvirtRepository(self.__db_conn)
            repo.set_col_order(["uuid", "name", "engine"])
            engines_repo = DBBasicRepository(self.__db_conn)
            engines_repo.set_model(OvirtEngine)
            engines_repo.set_base_query()
            engines, _ = engines_repo.build()
            engines = OrderedDict([("", "all")] + list(engines.items()))
            repo.set_filter_fields([
                {"name": "name", "type": "text", "default_value": ''},
                {"name": "engine", "type": "option", "options": engines}
            ])
            repo.set_filter_fields(["name", "engine"])
            return repo
        if repo_name == "VmOvirt":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(Vm)
            repo.set_col_order(["uuid", "name", "engine", "ip", "href"])
            engines_repo = DBBasicRepository(self.__db_conn)
            engines_repo.set_model(OvirtEngine)
            engines_repo.set_base_query()
            engines, _ = engines_repo.build()
            engines = {engine.name: engine.name for engine in engines}
            engines = OrderedDict([("", "all")] + list(engines.items()))
            repo.set_filter_fields([
                {"name": "uuid", "type": "text", "default_value": ''},
                {"name": "name", "type": "text", "default_value": ''},
                {"name": "ip", "type": "text", "default_value": ''},
                {"name": "engine", "type": "option", "options": engines}
            ])
            return repo
        if repo_name == "HostOvirt":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(Host)
            repo.set_col_order(["uuid", "name", "engine", "ip", "href"])
            engines_repo = DBBasicRepository(self.__db_conn)
            engines_repo.set_model(OvirtEngine)
            engines_repo.set_base_query()
            engines, _ = engines_repo.build()
            engines = {engine.name: engine.name for engine in engines}
            engines = OrderedDict([("", "all")] + list(engines.items()))
            repo.set_filter_fields([
                {"name": "uuid", "type": "text", "default_value": ''},
                {"name": "name", "type": "text", "default_value": ''},
                {"name": "ip", "type": "text", "default_value": ''},
                {"name": "engine", "type": "option", "options": engines}
            ])
            return repo
        if repo_name == "ClusterOvirt":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(Cluster)
            repo.set_col_order(["uuid", "name", "engine", "href"])
            engines_repo = DBBasicRepository(self.__db_conn)
            engines_repo.set_model(OvirtEngine)
            engines_repo.set_base_query()
            engines, _ = engines_repo.build()
            engines = {engine.name: engine.name for engine in engines}
            engines = OrderedDict([("", "all")] + list(engines.items()))
            repo.set_filter_fields([
                {"name": "uuid", "type": "text", "default_value": ''},
                {"name": "name", "type": "text", "default_value": ''},
                {"name": "engine", "type": "option", "options": engines}
            ])
            return repo
        if repo_name == "DataCenterOvirt":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(DataCenter)
            repo.set_col_order(["uuid", "name", "engine", "href"])
            engines_repo = DBBasicRepository(self.__db_conn)
            engines_repo.set_model(OvirtEngine)
            engines_repo.set_base_query()
            engines, _ = engines_repo.build()
            engines = {engine.name: engine.name for engine in engines}
            engines = OrderedDict([("", "all")] + list(engines.items()))
            repo.set_filter_fields([
                {"name": "uuid", "type": "text", "default_value": ''},
                {"name": "name", "type": "text", "default_value": ''},
                {"name": "engine", "type": "option", "options": engines}
            ])
            return repo
        if repo_name == "StorageOvirt":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(Storage)
            repo.set_col_order([
                "uuid", "name", "engine", "available", "used", "committed",
                "total", "percent_left", "href"
            ])
            engines_repo = DBBasicRepository(self.__db_conn)
            engines_repo.set_model(OvirtEngine)
            engines_repo.set_base_query()
            engines, _ = engines_repo.build()
            engines = {engine.name: engine.name for engine in engines}
            engines = OrderedDict([("", "all")] + list(engines.items()))
            repo.set_filter_fields([
                {"name": "uuid", "type": "text", "default_value": ''},
                {"name": "name", "type": "text", "default_value": ''},
                {"name": "engine", "type": "option", "options": engines},
            ])
            return repo
        if repo_name == "Backups":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(Backups)
            repo.set_col_order(
                ["name", "created", "type", "size", "source_key"]
            )
            repo.set_filter_fields([
                {"name": "uuid", "type": "text", "default_value": ''},
                {"name": "name", "type": "text", "default_value": ''}
            ])
            return repo
        if repo_name == "ElmaVm":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(ElmaVM)
            repo.set_col_order(["id", "name", "administrators"])
            repo.set_filter_fields([
                {"name": "id", "type": "text", "default_value": ''},
                {"name": "name", "type": "text", "default_value": ''}
            ])
            return repo
        if repo_name == "ElmaVmAccessDoc":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(ElmaVmAccessDoc)
            repo.set_col_order(["id", "doc_id", "name", "dns", "backup"])
            repo.set_filter_fields([
                {"name": "id", "type": "text", "default_value": ''},
                {"name": "doc_id", "type": "text", "default_value": ''},
                {"name": "name", "type": "text", "default_value": ''},
                {"name": "dns", "type": "text", "default_value": ''},
                {"name": "backup", "type": "text", "default_value": ''}
            ])
            return repo
        if repo_name == "ToBeBackedUpVms":
            repo = ToBeBackedUpVmsRepository(self.__db_conn)
            repo.set_col_order(["uuid", "name", "engine"])
            engines_repo = DBBasicRepository(self.__db_conn)
            engines_repo.set_model(OvirtEngine)
            engines_repo.set_base_query()
            engines, _ = engines_repo.build()
            engines = {engine.name: engine.name for engine in engines}
            engines = OrderedDict([("", "all")] + list(engines.items()))
            repo.set_filter_fields([
                {"name": "name", "type": "text", "default_value": ''},
                {"name": "engine", "type": "option", "options": engines},
                {"name": "show_dbs", "type": "check"},
                {"name": "show_absent_in_ov", "type": "check"},
            ])
            return repo
        if repo_name == "OvirtEngines":
            repo = DBBasicRepository(self.__db_conn)
            repo.set_model(OvirtEngine)
            repo.set_col_order(["id", "name", "href"])
            repo.set_filter_fields({})
            return repo
        if repo_name == "TapedOnlyVms":
            repo = TapedOnlyVmsRepository(self.__db_conn)
            repo.set_col_order(["uuid", "name", "size", "source_key", "type"])
            repo.set_filter_fields([
                {"name": "name", "type": "text", "default_value": ''},
                {"name": "type", "type": "option", "options":
                    {"":"all", "full": "full", "incremental": "incremental"}
                }
            ])
            return repo
        raise ValueError("'repo_name' is invalid.")
