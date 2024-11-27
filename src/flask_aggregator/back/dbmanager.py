"""Database interactions module."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from sqlalchemy.exc import IntegrityError
from .models import Base
from .logger import Logger

class DBManager():
    """Class that operates with Postgres database."""
    USERNAME = "aggregator"
    PASSWORD = "CnfhnjdsqGfhjkm%401234"
    DB_NAME = "aggregator_test"
    DB_ADDRESS = "10.105.253.252"
    DB_PORT = "6298"
    DATABASE_URL = (
        f"postgresql+psycopg2://{USERNAME}:{PASSWORD}@{DB_ADDRESS}"
        f":{DB_PORT}/{DB_NAME}"
    )

    def __init__(self) -> None:
        self.__engine = create_engine(self.DATABASE_URL)
        self.__session = scoped_session(sessionmaker(bind=self.__engine))
        Base.metadata.create_all(self.__engine)
        self.__logger = Logger()

    def add_data(self, data: list) -> None:
        """Add data to tables based on their type."""
        session = self.__session()
        for element in data:
            try:
                session.merge(element)
                session.commit()
                self.__logger.log_debug(
                    f"Added element with {element.uuid} of type "
                    f"{type(element).name}."
                )
            except IntegrityError:
                session.rollback()
                self.__logger.log_debug(
                    f"Element with same UUID ({element.uuid}) already "
                    "exists."
                )
            finally:
                session.close()

    def get_paginated_data(self, table_type, page, per_page, filters) -> tuple:
        """Get all data from specified table by type, paginated.
        Also get item count.
        """
        session = self.__session()
        query = session.query(table_type)
        query = self.__apply_filters(query, table_type, filters)
        total_items = query.count()
        query = query.offset((page - 1) * per_page).limit(per_page)
        data = query.all()
        session.close()
        return (total_items, data)

    def get_all_data_as_dict(self, table_type) -> dict:
        """For """
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
