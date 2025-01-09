"""Database interactions module."""

import os
from datetime import datetime, timedelta

from sqlalchemy import (
    create_engine, asc, desc, text, func, Table, MetaData
)
from sqlalchemy.sql import table
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, scoped_session, Query, aliased
from sqlalchemy.schema import DDLElement
from sqlalchemy.dialects.postgresql import insert
from flask_aggregator.config import ProductionConfig, DevelopmentConfig
from flask_aggregator.back.models import (
    Base,
    BackupsView,
    ElmaVM,
    Backups,
    ElmaVmAccessDoc,    # TODO: temp for testing make_join_query
    Vm                  # TODO: temp for testing make_join_query
)
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
            session = self.__session()
            # Create view cb_backups_view. First view for backups, it shows
            # only vms that were backed up by Cyberbackup.
            self.__create_view(
                session,
                "cb_backups_view",
                Queries.get_cb_backups_view_query(session)
            )
            # Main view for backed up VMs. It is a join between 3 tables
            # (two tables and one view): `vms` table (which represents VMs in
            # RedVirt), `elma_vm_access_doc` (information about VM creation
            # in ELMA) and `cb_backups_view` (list of VMs, backed up by
            # Cyberbackup).
            cb_backups_view = Table(
                "cb_backups_view",
                MetaData(),
                autoload_with=self.__engine
            )
            self.__create_view(
                session,
                "backups_view",
                Queries.get_backups_view_query(session, cb_backups_view)
            )
            # Get view for all VMs that need to be backed up. It is created by
            # joining `backups_view` (all backed up VMs that should be backed
            # up by ELMA) and `elma_vm_access_doc`.
            backups_view = Table(
                "backups_view",
                MetaData(),
                autoload_with=self.__engine
            )
            self.__create_view(
                session,
                "vms_to_be_backed_up_view",
                Queries.get_not_backed_up_vms(session, backups_view)
            )
            session.close()
        except OperationalError as e:
            self.__logger.log_error(e)

    @property
    def engine(self):
        """For external use."""
        return self.__engine

    def get_cb_backups_view(self) -> Table:
        """Return cb_backups_view view as `Table`."""
        return Table("cb_backups_view", MetaData(), autoload_with=self.__engine)

    def upsert_data(
        self,
        model: any,
        data: list,
        index_elements: list,
        included_elements: list
    ) -> None:
        """Upsert data to tables based on their type.
        
        Args:
            model (any): ORM db of sqlalchemy (class name).
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
        session = self.__session()
        # Postgres specific "upsert".
        stmt = insert(model).values(data)
        dict_set = {
            column.name: getattr(stmt.excluded, column.name)
            for column in model.__table__.columns
            if column.name not in included_elements
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=index_elements,
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
        session = self.__session()
        rows = None
        try:
            result = session.execute(query)
            rows = result.fetchall()
        except OperationalError as e:
            self.__logger.log_error(e)
        return rows

    def __make_join_query(
        self,
        # target_table: any,
        # join_tables: list,
        # target_fields: list,
    ) -> Query:
        # TODO: Check if tables are valid
        # TODO: Check if target fields are valid
        # Take multiple tables and multiple table fields.
        # Check if those are valid and exist in database/tables.
        # Generate conditions for JOIN query.
        # Make query for join on tables.
        # Apply filters to query. TODO: consider necessity
        session = self.__session()
        sq = (
            session.query(
                Backups.name,
                func.max(Backups.created).label("latest_created")
            )
            .group_by(Backups.name)
            .subquery()
        )        
        f_query = (
            session.query(ElmaVmAccessDoc.name)
            .filter(ElmaVmAccessDoc.name == Vm.name)
            .filter(ElmaVmAccessDoc.backup == True)
            .filter(ElmaVmAccessDoc.name == sq.c.name)
            .exists()
        )
        query = (
            session.query(
                Vm,
                ElmaVmAccessDoc,
                sq
            )
            .join(ElmaVmAccessDoc, Vm.name == ElmaVmAccessDoc.name)
            .join(sq, ElmaVmAccessDoc.name == sq.c.name)
            .filter(ElmaVmAccessDoc.backup == True)
        )
        e_query = (
            session.query(ElmaVmAccessDoc.name)
            .filter(ElmaVmAccessDoc.name == Vm.name)
            .filter(ElmaVmAccessDoc.backup == True)
            .filter(ElmaVmAccessDoc.name.like("%db%"))
            .filter(~f_query)
        )
        print(e_query)
        return e_query

    def get_query_result(self) -> list:    # TODO: remove debug
        query = self.__make_join_query()
        # print(query.all())
        result = []
        # for a, b in query:
        #     result.append({
        #         "vm_name": a.name,
        #         "backup": b.backup,
        #         # "backup_date": d
        #     })
        return query.all()

    def get_data_from_view(
        self, model: any
    ) -> list:
        """Get data from views only.
        
        If target is table ORM interaction is preferred.
        """
        session = self.__session()
        metadata = MetaData()
        view = Table(model.table_name(), metadata, autoload_with=self.__engine)
        query = session.query(view)
        print(query.all(), query)
        # total_items_query = text("select count(*) from backups_view;")
        # total_items = session.execute(total_items_query).all()
        # print(*total_items)
        # query = self.__prettify_query(
        #     query, model, page, per_page, fields, filters, sort_by, order
        # )
        result = self.__make_view_model_list(model, query)
        session.close()
        return (query.count(), result)

    def __make_view_model_list(
        self,
        model: any,
        query: Query
    ) -> list:
        result = []
        for row in query.all():
            result.append(model(
                id_=row[0],
                uuid_=row[1],
                name=row[2],
                engine=row[3],
            ))
        return result

    def __prettify_query(
        self, query: Query, model: any, page: int, per_page: int,
        fields: list, filters: list, sort_by: str, order: str
    ) -> Query:
        # Adding field selection. Only selected fields will be queried.
        # table_fields = [text(f) for f in fields if f in dir(model)]
        # query = query.with_entities(*table_fields)
        # Setting up filters, only specified entities will be found.
        # query = self.__apply_filters(query, model, filters)
        # Sorting.
        if order == "desc":
            query = query.order_by(desc(text(sort_by)))
        else:
            query = query.order_by(asc(text(sort_by)))
        # Paginating with offset.
        query = query.offset((page - 1) * per_page).limit(per_page)
        return query

    def __create_view(
        self,
        session: scoped_session,
        view_name: str,
        query: Query
    ) -> None:
        """Create view based on text query."""
        query = str(query.statement.compile(
            dialect=session.bind.dialect,
            compile_kwargs={"literal_binds": True}
        ))
        query = text(f"create or replace view {view_name} as {query};")
        session.execute(query)
        session.commit()
        session.close()

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
        if mode == "show":
            return query.filter(column.like(f"%{value}%"))
        if mode == "hide":
            return query.filter(~column.like(f"%{value}%"))
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

class Queries:
    """Class for storing various queries."""
    @staticmethod
    def get_cb_backups_view_query(session: scoped_session) -> Query:
        """Return unique backups query."""
        return session.query(
            Backups.name,
            func.max(Backups.created).label("latest_created")
        ).group_by(Backups.name)

    @staticmethod
    def get_backups_view_query(
        session: scoped_session,
        cb_backups_view: Table
    ) -> Query:
        """Return VMs only with existent backups."""
        query = (
            session.query(
                Vm.id.label("id"),
                Vm.uuid.label("uuid"),
                Vm.name.label("name"),
                Vm.engine.label("engine")
            )
            .join(ElmaVmAccessDoc, Vm.name == ElmaVmAccessDoc.name)
            .join(
                cb_backups_view,
                ElmaVmAccessDoc.name == cb_backups_view.c.name
            )
            .filter(ElmaVmAccessDoc.backup == True)
        )
        return query

    @staticmethod
    def get_not_backed_up_vms(
        session: scoped_session,
        backups_view: Table
    ) -> Query:
        """Return only not backed up VMs (but should be backed up by ELMA)."""
        backups_view_alias = aliased(backups_view)
        query = session.query(
                backups_view_alias.c.id,
                backups_view_alias.c.uuid,
                ElmaVmAccessDoc.name,
                backups_view_alias.c.engine
            ).outerjoin(
                backups_view_alias, backups_view_alias.c.name == ElmaVmAccessDoc.name
            ).outerjoin(
                Vm, Vm.name == ElmaVmAccessDoc.name
            ).filter(
                ElmaVmAccessDoc.backup == True,
                Vm.name == None,
                backups_view_alias.c.name == None
            ).filter(~ElmaVmAccessDoc.name.like("%db%"))
        print(query)
        return query
