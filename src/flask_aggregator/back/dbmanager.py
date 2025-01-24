"""Database interactions module."""

import os
from datetime import datetime, timedelta

from sqlalchemy import (
    create_engine, asc, desc, text, func, Table, MetaData
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, scoped_session, Query, aliased
from sqlalchemy.dialects.postgresql import insert
from flask_aggregator.config import ProductionConfig, DevelopmentConfig
from flask_aggregator.back.models import (
    Base,
    Storage,
    BackupsView,
    ElmaVM,
    Backups,
    ElmaVmAccessDoc,    # TODO: temp for testing make_join_query
    Vm,                  # TODO: temp for testing make_join_query
    VmsToBeBackedUpView
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
        except OperationalError as e:
            self.__logger.log_error(e)

    @property
    def engine(self):
        """For external use."""
        return self.__engine

    def generate_views(self) -> None:
        """Create all views."""
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

    def get_data_from_view(
        self,
        model: any,
        page: int,
        per_page: int,
        fields: list,
        filters: list,
        sort_by: str,
        order: str,
        **kwargs: any
    ) -> tuple:
        """Get data from views only.
        
        If target is table ORM interaction is preferred.

        Args:
            model (any): Model class (described in `models.py`).
            page (int): Current page, passed from HTML frontend to function.
            per_page (int): Element count per page in HTML view.
            fields (list): List of fields to be showed in HTML view.
            filters (list): Filter list.
            sort_by (str): Column name by which table is sorted.
            order (str): `asc` or `desc`.
            **kwargs (any): additional filters/parameters for function.
        """
        session = self.__session()
        metadata = MetaData()
        view = Table(model.table_name(), metadata, autoload_with=self.__engine)
        query = session.query(view)
        # Applying main filters.
        item_count, query = self.__prettify_query(
            query, model, fields, filters, sort_by, order
        )
        # If there are any other parameters except default.
        if kwargs:
            item_count, query = self.__apply_custom_filters(
                view, query, **kwargs
            )
        # Paginating with offset. Making this operation last so we don't lose
        # correct item count.
        query = query.offset((page - 1) * per_page).limit(per_page)
        session.close()
        return (item_count, query.all())

    def __apply_custom_filters(
        self,
        view: any,
        query: Query,
        **kwargs: any
    ) -> tuple:
        """Apply additional custom filters which are specific to a certain 
        table/view.
        """
        # `vms_to_be_backed_up_view`, showing/hiding database VMs.
        if (
            "show_dbs" in kwargs
            and isinstance(kwargs["show_dbs"], bool)
            and not kwargs["show_dbs"]
        ):
            # Showing only VMs with names that don't contain `db`.
            query = query.filter(~view.c.name.like("%db%"))
        # `vms_to_be_backed_up_view`, showing/hiding VMs absent in oVirt.
        if (
            "show_absent_in_ov" in kwargs
            and isinstance(kwargs["show_absent_in_ov"], bool)
            and not kwargs["show_absent_in_ov"]
        ):
            # If VM has no uuid it means it is absent in oVirt.
            query = query.filter(view.c.uuid != None)
        return (query.count(), query)

    def __prettify_query(
        self, query: Query, model: any, fields: list, filters: list,
        sort_by: str, order: str
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
        item_count = query.count()
        return (item_count, query)

    def __create_view(
        self,
        session: scoped_session,
        view_name: str,
        query: Query
    ) -> None:
        """Create view based on text query.
        
        Args:
            sessions (scoped_session): Current database sqlalchemy session.
            view_name (str): Desired view name.
            query (Query): Query, by which view should be created.
        """
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
        month_ago = datetime.now() - timedelta(days=30)
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
            query = (
                query
                .filter(table_type.created < two_days_ago)
                .filter(table_type.created > month_ago)
            )
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

    def get_data(self, table_type) -> list:
        """Get raw data from table."""
        session = self.__session()
        data = session.query(table_type).all()
        session.close()
        return data

    def get_item_count(self, table_type) -> int:
        """Get item count for current query."""
        session = self.__session()
        query = session.query(table_type)
        session.close()
        return query.count()

    def get_model_filters(self, table_type) -> list:
        """Get filters from model."""
        return table_type.get_filters()
    
    def get_model_columns(self, table_type) -> list:
        """Get fields from model."""
        return table_type.get_columns_order()

    def get_data_by_query(self) -> list:
        pass

    def get_taped_vms(self, table_type, **filters: any) -> None:
        """Get data by query and 'beautify' it."""
        query = Queries.get_tape_only_backups(self.__session)
        query = self.__apply_filters(query, table_type, filters)
        # Sorting.
        if filters["order"] == "desc":
            query = query.order_by(desc(filters["sort_by"]))
        else:
            query = query.order_by(asc(filters["sort_by"]))
        # Item count.
        total_items = query.count()
        # Paginating with offset.
        query = query.offset(
            (filters["page"] - 1) * filters["per_page"]
        ).limit(filters["per_page"])
        data = query.all()
        return total_items, data

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


class QueryBuilder():
    """Class for constructing complicated SQLAlchemy queries."""
    def __init__(self, session: scoped_session, base_query: Query):
        self.__session = session
        self.__base_query = base_query
        self.__filters = []
        self.__sorts = []
        self.__limit = None
        self.__offset = None

    def add_filter(self, condition):
        """Add filter to query."""
        self.__filters.append(condition)
        return self

    def add_sort(self, column, desc_=False):
        """Add sorting statement."""
        if desc_:
            self.__sorts.append(column.desc())
        else:
            self.__sorts.append(column.asc())
        return self

    def add_pagination(self, limit, offset):
        """Add 'pagination'."""
        self.__limit = limit
        self.__offset = offset
        return self

    def build(self):
        """Make query."""
        query = self.__base_query
        if self.__filters:
            query.filter(*self.__filters)
        if self.__sorts:
            query.order_by(*self.__sorts)
        if self.__limit is not None:
            query = query.limit(self.__limit)
        if self.__offset is not None:
            query = query.offset(self.__offset)
        return query

    def execute(self):
        """Execute query."""
        query = self.build()

        data = self.__session.execute(query).scalars().all()

        item_count = self.__base_query.filter(*self.__filters).count()

        return data, item_count


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
                Vm.id,
                Vm.uuid,
                ElmaVmAccessDoc.name,
                Vm.engine
            ).outerjoin(
                backups_view_alias,
                backups_view_alias.c.name == ElmaVmAccessDoc.name
            ).outerjoin(
                Vm, Vm.name == ElmaVmAccessDoc.name
            ).filter(
                ElmaVmAccessDoc.backup == True,
                backups_view_alias.c.name == None
            )
        return query

    @staticmethod
    def get_all_data(
        session: scoped_session,
        table_: Table
    ) -> Query:
        """Return query `select * from table;`."""
        return session.query(table_).all()

    @staticmethod
    def get_tape_only_backups(
        session: scoped_session
    ) -> Query:
        """Return only those VMs that are backed up to tape."""        
        filtered_query = session.query(Backups).filter(
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
        print(subquery.count())
        subquery = subquery.subquery()
        query = (
            session.query(Backups)
            .join(
                subquery,
                (Backups.name == subquery.c.name)
                & (Backups.created == subquery.c.latest_created)
                & (Backups.source_key.like("%POOL%"))
            )
        )
        return query
