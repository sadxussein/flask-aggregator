"""Test module for database interactions architecture."""

from abc import ABC, abstractmethod

from sqlalchemy import create_engine, func, asc, desc
from sqlalchemy.orm import scoped_session, sessionmaker

from flask_aggregator.back.models import Backups


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

    # def __init__(self, engine: any):
    #     self.__md = MetaData()
    #     self.__e = engine
    #     self.__ents = []

    # # TODO: read about Alembic!
    # def create_table(self, t: Table) -> None:
    #     """Create table/view in database."""
    #     self.__md.create_all(bind=self.__e, tables=[t])

    # def create_all_tables(self) -> None:
    #     """Create all tables/views in database."""
    #     self.__md.create_all(bind=self.__e)

    # def drop_table(self, t: Table) -> None:
    #     """Remove table/view from database."""
    #     self.__md.drop_all(bind=self.__e, tables=[t])

    # def drop_all_tables(self) -> None:
    #     """Remove all tables/views from database."""
    #     self.__md.drop_all(bind=self.__e)


class DBRepository(ABC):
    """Abstract class for different variants of database interactions.

    Driver may vary.
    """
    def __init__(self, conn: DBConnection):
        self._s = conn.get_scoped_session()
        self._query = None

    @property
    def data(self) -> list:
        """Return data as list."""
        if self._query is None:
            raise ValueError("Query is empty!")
        if self._query.all() is None:
            raise ValueError("Data is empty!")
        return self._query.all()

    @abstractmethod
    def set_base_query(self):
        """Base query for current database interaction (repository)."""

    @abstractmethod
    def set_filter(self, **kwargs: any):
        """Set filters, based on which SQL statement will be created."""        

    @abstractmethod
    def set_order(self, col_name: str, order: str):
        """Set asc/desc order of items.

        Args:
            col_name (str): Name of the column in the table.
            order (str): Will be sorted in ascending if order is `asc`, 
                descending otherwise.
        """

    @abstractmethod
    def set_pagination(self, per_page: int, page: int):
        """Set items per page and current page.

        Args:
            per_page (int): Item count to be shows per page.
            page (int): Current page index.
        """

    @abstractmethod
    def upsert_data(
        self, data: list, index_elements: list, included_elements: list
    ) -> None:
        """Upsert data to tables based on their type.

        Args:
            data (list): Data, either list of dicts (with all fields of model)
                or list of model elements (i.e. derived from Base ORM class).
            index_elements (list): List or strings, representing fields
                (columns), which have to be excluded from ON CONFLICT clause
                (to the right side of the clausee).
            included_elements (list): List of strings, representing elements
                to be excluded from the right side of DO UPDATE SET (these
                elements will not be updated on conflict).

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

    def set_filter(self, **kwargs: any):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply filter to empty query."
            )
        if kwargs:
            for k, v in kwargs.items():
                if v != '' and v is not None:
                    col = getattr(Backups, k, None)
                    if col is not None:
                    # TODO: need to think about strict and non-strict search
                        self._query = self._query.filter(col.like(f"%{v}%"))
        return self

    def set_order(self, col_name: str, order: str):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply order_by to empty query."
            )
        col = getattr(Backups, col_name, None)
        if col is not None:
            if order == "asc":
                self._query.order_by(asc(col))
            else:
                self._query.order_by(desc(col))
        return self

    def set_pagination(self, per_page: int, page: int):
        if self._query is None:
            raise ValueError(
                "Query is 'None'. Can't apply offset and limit to empty "
                "query."
            )
        self._query = (
            self._query.offset((page - 1) * per_page).limit(per_page)
        )
        return self

    def upsert_data(
        self, data: list, index_elements: list, included_elements: list
    ) -> None:
        pass
