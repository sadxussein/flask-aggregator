"""Database interactions module."""

from datetime import datetime, timedelta

from sqlalchemy import create_engine, asc, desc, text, select, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from sqlalchemy.dialects.postgresql import insert
from flask_aggregator.config import ProductionConfig, DevelopmentConfig
from flask_aggregator.back.models import Base, Backups
from flask_aggregator.back.logger import Logger

class DBManager():
    """Class that operates with Postgres database."""
    def __init__(
        self, db_url: str=None, env: str="dev", logger=Logger()
    ) -> None:
        self.__logger = logger
        if db_url is None:
            if env == "prod":
                self.__engine = create_engine(ProductionConfig.DB_URL)
            else:
                self.__engine = create_engine(DevelopmentConfig.DB_URL)
        else:
            self.__engine = create_engine(db_url)
        self.__session = scoped_session(sessionmaker(bind=self.__engine))
        try:
            Base.metadata.create_all(self.__engine)
        except OperationalError as e:
            self.__logger.log_error(e)

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

    def get_old_backups(
            self, table_type, page, per_page, filters, sort_by: str,
            order: str, fields: list
    ) -> tuple:
        """Get backups older than 2 days.""" 
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
            .filter(table_type.created < two_days_ago)
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


