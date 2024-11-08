"""Database interactions module."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
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
        self.__engine = create_engine(self.DATABASE_URL, echo=True)
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
                self.__logger.log_error(
                    f"Element with same UUID ({element.uuid}) already "
                    "exists."
                )
            finally:
                session.close()

    def get_all_data(self, table_type) -> list:
        """Get all data from specified table by type."""
        session = self.__session()
        data = session.query(table_type).all()
        session.close()
        return data

    def get_paginated_data(self, table_type, page, per_page) -> list:
        """Get all data from specified table by type, paginated."""
        session = self.__session()
        data = (
            session.query(table_type)
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        data = data.all()
        session.close()
        return data

    def get_data_count(self, table_type) -> int:
        """Number of lines in selected table.

        Takes class name as an argument.
        """
        session = self.__session()
        count = session.query(table_type).count()
        return count

    def close(self):
        """Clean up and close."""
        self.__session.remove()
        self.__engine.dispose()
