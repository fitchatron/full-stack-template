from collections.abc import Sequence
from typing import Any, TypeVar

from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import (
    ColumnElement,
    Delete,
    Select,
    Update,
    delete,
    insert,
    inspect,
    select,
    tuple_,
    update,
)
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.schemas.order_by_generator import OrderByCondition
from app.schemas.pagination import OptionalPage
from app.utils.exception import NoOrderByColumnsSpecified
from app.utils.order_by_generator import OrderByGenerator

ModelType = TypeVar("ModelType")
Schema = TypeVar("Schema")


class CRUDRepository[ModelType, Schema]:
    """
    CRUD repository base. Comes with all CRUD method that can be performed on a basic model.
    """

    def __init__(self, session: Session, model: type[ModelType]) -> None:
        """
        CRUD Repository constructor
        """

        self.session = session
        self.model = model

    def create_single_item(self, values: dict, commit: bool = True) -> ModelType | None:
        """
        Create a single item in the database and return a the Schema instance if successful.
        """

        sql = insert(self.model).values(**values)

        # return inserted record
        sql = sql.returning(self.model)

        # execute sql
        result = self.session.scalars(sql).first()

        if commit:
            self.session.commit()

        if result is not None:
            self.session.refresh(result)

        return result

    def create_multiple_items(
        self, data: list[dict], commit: bool = True
    ) -> Sequence[ModelType] | None:
        """
        Create many items in the database and return a list if successful.
        """
        sql = insert(self.model).values(data)

        # return inserted record
        sql = sql.returning(self.model)

        # execute sql
        result = self.session.scalars(sql).all()

        if commit:
            self.session.commit()

        return result

    def _build_select(
        self,
        filters: ColumnElement[bool] | None = None,
        sort_by: list[OrderByCondition] | None = None,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> Select[tuple[ModelType]]:
        """
        Build a select statement with optional joins, filters and order by
        """

        sql = select(self.model)

        if joins:
            for join in joins:
                sql = sql.join(join)

        # construct where clause if filters provided
        if filters is not None:
            sql = sql.where(filters)

        # construct order by
        if sort_by:
            generator = OrderByGenerator(model=self.model)
            order = generator.build_order_conditional(sort_by)
            sql = sql.order_by(*order)

        return sql

    def _apply_filters[Statement: (Update, Delete)](
        self,
        sql: Statement,
        filters: ColumnElement[bool],
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> Statement:
        """
        Apply filters to an update or delete statement.
        UPDATE/DELETE can't join directly, so when joins are provided the filters are
        applied to a select of the primary keys and the statement targets those rows.
        """

        if not joins:
            return sql.where(filters)

        mapper = inspect(self.model)
        if mapper is None:
            raise ValueError(f"Model {self.model} is not mapped")

        pks = mapper.primary_key

        subquery = select(*pks).select_from(self.model)

        for join in joins:
            subquery = subquery.join(join)

        subquery = subquery.where(filters)

        if len(pks) > 1:
            return sql.where(tuple_(*pks).in_(subquery))

        return sql.where(pks[0].in_(subquery))

    def read_single_item(
        self,
        filters: ColumnElement[bool],
        sort_by: list[OrderByCondition] | None = None,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> ModelType | None:
        """
        Read a single item by specifying filters
        """

        sql = self._build_select(filters, sort_by, joins)
        return self.session.scalars(sql).first()

    def read_by_pk(self, pk: Any) -> ModelType | None:
        return self.session.get(self.model, pk)

    def read_multiple_items(
        self,
        filters: ColumnElement[bool] | None = None,
        sort_by: list[OrderByCondition] | None = None,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> Sequence[ModelType]:
        """
        Read many items by specifying filters.
        """

        sql = self._build_select(filters, sort_by, joins)
        return self.session.scalars(sql).all()

    def read_paginated_items(
        self,
        sort_by: list[OrderByCondition],
        filters: ColumnElement[bool] | None = None,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> OptionalPage[ModelType]:
        """
        Read a page of items by specifying filters.
        At least 1 order by column is required so pages are stable.
        """

        if not sort_by:
            raise NoOrderByColumnsSpecified(
                "At least 1 order by column must be specified."
            )

        sql = self._build_select(filters, sort_by, joins)
        return paginate(self.session, sql)

    def update_single_item(
        self,
        filters: ColumnElement[bool],
        values: dict,
        commit: bool = True,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> ModelType | None:
        """
        Update a single item by specifying filters and new values.
        Filters must identify at most one row
        """
        sql = update(self.model).values(**values)

        sql = self._apply_filters(sql, filters, joins)

        # return updated records
        sql = sql.returning(self.model)

        # execute sql
        result = self.session.scalars(sql).one_or_none()

        if commit:
            self.session.commit()

        return result

    def update_multiple_items_with_same_values(
        self,
        filters: ColumnElement[bool],
        values: dict,
        commit: bool = True,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> Sequence[ModelType]:
        """
        Update multiple items with the same values.
        When updating multiple rows, the updated rows are returned.
        """

        sql = update(self.model).values(**values)

        sql = self._apply_filters(sql, filters, joins)

        # return updated records
        sql = sql.returning(self.model)

        # execute sql
        results = self.session.scalars(sql).all()

        if commit:
            self.session.commit()

        return results

    def update_multiple_items_with_different_values(
        self,
        filters: ColumnElement[bool] | None,
        parameters: list[dict],
        commit: bool = True,
    ) -> None:
        """
        Update multiple items with different values.
        When updating multiple rows, the updated rows are not returned.
        Limitation from SQLAlchemy.
        Parameters should be a list of dictionaries, where each dictionary contains the
        primary key and the fields to be updated.
        E.g. [{"id": 1, "name": "new name"}, {"id": 2, "name": "another new name"}]

        DO NOT try and update dates using the sqlalchemy dates e.g. func.now(). It will fail
        """

        sql = update(self.model).execution_options(synchronize_session=None)

        # construct where clause if filters provided
        if filters is not None:
            sql = sql.where(filters)

        self.session.execute(sql, parameters)

        if commit:
            self.session.commit()

    def delete_single_item(
        self,
        filters: ColumnElement[bool],
        commit: bool = True,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> ModelType | None:
        """
        Delete a single row. When deleting a single row, the deleted row is returned.
        The returned row is detached from the session so its column values stay readable
        after commit. Relationships on it can't be lazy loaded.
        """

        sql = delete(self.model)

        sql = self._apply_filters(sql, filters, joins)

        sql = sql.returning(self.model)

        # execute sql
        result = self.session.scalars(sql).one_or_none()

        # detach so commit doesn't expire the row, which no longer exists to be reloaded
        if result is not None:
            self.session.expunge(result)

        if commit:
            self.session.commit()

        return result

    def delete_multiple_items(
        self,
        filters: ColumnElement[bool],
        commit: bool = True,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> Sequence[ModelType]:
        """
        Delete multiple rows. When deleting multiple rows, the deleted rows are returned.
        The returned rows are detached from the session so their column values stay
        readable after commit. Relationships on them can't be lazy loaded.
        """

        sql = delete(self.model)

        sql = self._apply_filters(sql, filters, joins)

        sql = sql.returning(self.model)

        # execute sql
        results = self.session.scalars(sql).all()

        # detach so commit doesn't expire the rows, which no longer exist to be reloaded
        for result in results:
            self.session.expunge(result)

        if commit:
            self.session.commit()

        return results
