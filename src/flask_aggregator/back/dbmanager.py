"""Database interactions module."""

from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker, scoped_session, Query
from sqlalchemy.dialects.postgresql import insert
from flask_aggregator.config import ProductionConfig, DevelopmentConfig
from flask_aggregator.back.models import Base

class DBManager():
    """Class that operates with Postgres database."""
    def __init__(self, db_url: str=None, env: str="prod") -> None:
        if db_url == None:
            if env == "prod":
                self.__engine = create_engine(ProductionConfig.DB_URL)
            else:
                self.__engine = create_engine(DevelopmentConfig.DB_URL)
        else: 
            self.__engine = create_engine(db_url)
        self.__session = scoped_session(sessionmaker(bind=self.__engine))
        Base.metadata.create_all(self.__engine)

    def add_data(self, model: any, data: list) -> None:
        """Add data to tables based on their type."""
        session = self.__session()
        # Postgres specific "upsert".
        stmt = insert(model).values(data)
        dict_set = {
            column.name: getattr(stmt.excluded, column.name)
            for column in model.__table__.columns if column.name != 'uuid'
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=['uuid'],
            set_=dict_set
        )
        session.execute(stmt)
        session.commit()
        session.close()

    def get_paginated_data(
            self, table_type, page, per_page, filters, sort_by: str,
            order: str
    ) -> tuple:
        """Get all data from specified table by type, paginated.
        Also get item count.
        """
        session = self.__session()
        query = session.query(table_type)
        query = self.__apply_filters(query, table_type, filters)
        if order == "desc":
            query = query.order_by(desc(sort_by))
        else:
            query = query.order_by(asc(sort_by))
        total_items = query.count()
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
