"""Database interactions module."""

import os
from datetime import datetime, timedelta

from sqlalchemy import create_engine, asc, desc, text, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from sqlalchemy.dialects.postgresql import insert
from flask_aggregator.config import ProductionConfig, DevelopmentConfig
from flask_aggregator.back.models import Base, ElmaVM, Backups
from flask_aggregator.back.logger import Logger

class DBManager():
    """Class that operates with Postgres database."""
    def __init__(
        self, db_url: str=None, env: str=os.getenv("FA_ENV"), logger=Logger()
    ) -> None:
        self.__logger = logger
        # Checking if there is ENV variable `FA_ENV`. If there is and it
        # either 'prod' or 'dev' value there - put it to `env` class variable.
        if db_url is None:
            if env == "dev":
                self.__engine = create_engine(DevelopmentConfig.DB_URL)
            else:
                self.__engine = create_engine(ProductionConfig.DB_URL)
        else:
            self.__engine = create_engine(db_url)
        self.__session = scoped_session(sessionmaker(bind=self.__engine))
        try:
            Base.metadata.create_all(self.__engine)
        except OperationalError as e:
            self.__logger.log_error(e)

    @property
    def engine(self):
        """For external use."""
        return self.__engine

    def upsert_data(self, model: any, data: list) -> None:
        """Upsert data to tables based on their type."""
        session = self.__session()
        # Postgres specific "upsert".
        stmt = insert(model).values(data)
        dict_set = {
            column.name: getattr(stmt.excluded, column.name)
            for column in model.__table__.columns
            if column.name not in ["id", "uuid"]
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=["uuid"],
            set_=dict_set
        )
        session.execute(stmt)
        session.commit()
        session.close()

    def add_data(self, data: list) -> None:
        """Add data to tables based on their type."""
        session = self.__session()
        session.add_all(data)
        session.commit()
        session.close()

    def run_simple_query(self, query_string: str) -> tuple:
        """Run simple text query and get its result."""
        query = text(query_string)
        session = self.__session
        rows = None
        try:
            result = session.execute(query)
            rows = result.fetchall()
        except OperationalError as e:
            self.__logger.log_error(e)
        return rows

    def get_elma_backups(
            self, page, per_page, filters, sort_by: str,
            order: str, fields: list, backups_to_show: str, show_dbs: str
    ) -> tuple:
        """Get Elma + Backups join and full Elma backup list."""
        session = self.__session()
        # Main query.
        query = session.query(ElmaVM)
        # Showing only vms with names that contain 'db'.
        query = self.__apply_field_like_filter(
            ElmaVM.name, query, show_dbs, "db"
        )

        if backups_to_show == "join":
            sq = (
                    session.query(Backups.name)
                    .filter(Backups.name == ElmaVM.name)
                    .exists()
                )
            query = query.filter(
                ElmaVM.should_be_backuped == "Да",
                ~sq.correlate(ElmaVM)
            )
            print(query.count())
        else:
            query = session.query(ElmaVM)

        # Adding field selection. Only selected fields will be queried.
        table_fields = [getattr(ElmaVM, f) for f in fields]
        query = query.with_entities(*table_fields)
        # Setting up filters, only specified entities will be found.
        query = self.__apply_filters(query, ElmaVM, filters)
        # Sorting.
        if order == "desc":
            query = query.order_by(desc(sort_by))
        else:
            query = query.order_by(asc(sort_by))
        # Item count.
        total_items = query.count()
        # Paginating with offset.
        query = query.offset((page - 1) * per_page).limit(per_page)

        data = query.all()
        return (total_items, data)

    def __apply_field_like_filter(
        self, column: any, query: Query, mode: str, value: str
    ) -> Query:
        """Add LIKE filter to query.
        
        Args:
            column (any): ORM sqlalchemy table column.
            query (Query): Where filter should be applied.
            mode (str): 'show', 'hide' or 'all'. Last value disables filter if
                if was previously enabled.
            value (str): filtering value.
        """
        if mode == "all":
            return query
        elif mode == "show":
            return query.filter(column.like(f"%{value}%"))
        elif mode == "hide":
            return query.filter(~column.like(f"%{value}%"))
        else:
            raise KeyError(
                "Bad mode, should be 'all', 'show' or 'hide'. Check input."
            )

    def get_old_backups(
            self, table_type, page, per_page, filters, sort_by: str,
            order: str, fields: list, backups_to_show: str
    ) -> tuple:
        """Get backups older than 2 days or newer than 2 days.""" 
        session = self.__session()
        # Main query and subquery.
        subquery = (
            session.query(
                table_type.name,
                func.max(table_type.created).label("latest_created")
            )
            .group_by(table_type.name)
            .subquery()
        )
        two_days_ago = datetime.now() - timedelta(days=2)
        query = (
            session.query(table_type)
            .join(
                subquery,
                (table_type.name == subquery.c.name)
                & (table_type.created == subquery.c.latest_created)
            )
        )
        if backups_to_show == "older":    # older than 2 days old.
            query = query.filter(table_type.created < two_days_ago)
        elif backups_to_show == "less":   # less than 2 days old.
            query = query.filter(table_type.created >= two_days_ago)
        elif backups_to_show == "all":      # all backups.
            pass
        # Showing elma and CB present backups.
        elif backups_to_show == "elma_join":
            elma_query = (
                session.query(ElmaVM)
                .filter(
                    ElmaVM.should_be_backuped == "Да",
                    ElmaVM.is_deleted == "Нет"
                )
                .subquery()
            )
            query = query.join(
                elma_query, elma_query.c.name == table_type.name
            )

        # Adding field selection. Only selected fields will be queried.
        table_fields = [getattr(table_type, f) for f in fields]
        query = query.with_entities(*table_fields)
        # Setting up filters, only specified entities will be found.
        query = self.__apply_filters(query, table_type, filters)
        # Sorting.
        if order == "desc":
            query = query.order_by(desc(sort_by))
        else:
            query = query.order_by(asc(sort_by))
        # Item count.
        total_items = query.count()
        # Paginating with offset.
        query = query.offset((page - 1) * per_page).limit(per_page)

        data = query.all()
        return (total_items, data)

    def get_paginated_data(
            self, table_type, page, per_page, filters, sort_by: str,
            order: str, fields: list
    ) -> tuple:
        """Get all data from specified table by type, paginated.
        Also get item count.
        """
        session = self.__session()
        # Setting query for a certain table.
        query = session.query(table_type)
        # Adding field selection. Only selected fields will be queried.
        table_fields = [getattr(table_type, f) for f in fields]
        query = query.with_entities(*table_fields)
        # Setting up filters, only specified entities will be found.
        query = self.__apply_filters(query, table_type, filters)
        # Sorting.
        if order == "desc":
            query = query.order_by(desc(sort_by))
        else:
            query = query.order_by(asc(sort_by))
        # Item count.
        total_items = query.count()
        # Paginating with offset.
        query = query.offset((page - 1) * per_page).limit(per_page)
        data = query.all()
        session.close()
        return (total_items, data)

    def get_all_data_as_dict(self, table_type) -> dict:
        """For aggregator client parser."""
        session = self.__session()
        data = session.query(table_type).all()
        dict_data = [d.as_dict for d in data]
        session.close()
        return dict_data

    def __apply_filters(
        self, query: Query, table_type: any, filters: dict
    ) -> Query:
        """Apply query filters."""
        for k, v in filters.items():
            if v != '' and v is not None:
                column = getattr(table_type, k, None)
                if column is not None:
                    query = query.filter(column.like(f"%{v}%"))
        return query

    def close(self):
        """Clean up and close."""
        self.__session.remove()
        self.__engine.dispose()


