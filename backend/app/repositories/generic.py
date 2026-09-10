from sqlalchemy import select, update, insert, delete, inspect, tuple_
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from typing import Type, Generic, TypeVar, Optional, Sequence
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.links import Page

from app.utils.exception import NoOrderByColumnsSpecified
from app.schemas.order_by_generator import OrderByCondition
from app.utils.order_by_generator import OrderByGenerator
from app.schemas.filter_generator import FilterPayload
from app.utils.filter_generator import FilterGenerator

ModelType = TypeVar("ModelType")
Schema = TypeVar("Schema")


class CRUDRepository(Generic[ModelType, Schema]):
    """
    CRUD repository base. Comes with all CRUD method that can be performed on a basic model.
    """

    def __init__(self, session: Session, model: Type[ModelType]) -> None:
        """
        CRUD Repository constructor
        """

        self.session = session
        self.model = model

    def create_single_item(
        self, values: dict, commit: bool = True
    ) -> Optional[ModelType]:
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
    ) -> Optional[Sequence[ModelType]]:
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

    def read_single_item(
        self,
        filters: FilterPayload,
        sort_by: list[OrderByCondition] | None = None,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> Optional[ModelType]:
        """
        Read a single item by specifying filters
        """

        sql = select(self.model)

        if joins:
            for join in joins:
                sql = sql.join(join)

        # construct where clause
        filter_generator = FilterGenerator(model=self.model)
        filter_clause = filter_generator.build_filter(filters)
        sql = sql.where(filter_clause)

        # construct order by
        if sort_by:
            generator = OrderByGenerator(model=self.model)
            order = generator.build_order_conditional(sort_by)
            sql = sql.order_by(*order)

        return self.session.scalars(sql).first()

    def read_multiple_items(
        self,
        filters: FilterPayload | None = None,
        sort_by: list[OrderByCondition] | None = None,
        paginate_results: bool = True,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> Page[Schema] | Sequence[ModelType]:
        """
        Read many items by specifying filters.
        Results can be paginated.
        """

        # ensure order by column is specified for pagination
        if paginate_results and sort_by is None:
            raise NoOrderByColumnsSpecified(
                "At least 1 order by column must be specified."
            )

        sql = select(self.model)

        if joins:
            for join in joins:
                sql = sql.join(join)

        # construct where clause if filters provided
        if filters is not None:
            filter_generator = FilterGenerator(model=self.model)
            filter_clause = filter_generator.build_filter(filters)
            sql = sql.where(filter_clause)

        # construct order by
        if sort_by:
            generator = OrderByGenerator(model=self.model)
            order = generator.build_order_conditional(sort_by)
            sql = sql.order_by(*order)

        return (
            paginate(self.session, sql)
            if paginate_results
            else self.session.scalars(sql).all()
        )

    def update_multiple_items_with_same_values(
        self,
        filters: FilterPayload,
        values: dict,
        commit: bool = True,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> Sequence[ModelType]:
        """
        Update multiple items with the same values.
        When updating multiple rows, the updated rows are returned.
        """

        sql = update(self.model).values(**values)

        # construct where clause
        filter_generator = FilterGenerator(model=self.model)
        filter_clause = filter_generator.build_filter(filters)

        if joins:
            mapper = inspect(self.model)
            if mapper is None:
                raise ValueError(f"Model {self.model} is not mapped")

            pks = mapper.primary_key

            subquery = select(*pks).select_from(self.model)

            for join in joins:
                subquery = subquery.join(join)

            subquery = subquery.where(filter_clause)

            if len(pks) > 1:
                sql = sql.where(tuple_(*pks).in_(subquery))
            else:
                sql = sql.where(pks[0].in_(subquery))
        else:
            sql = sql.where(filter_clause)

        # return updated records
        sql = sql.returning(self.model)

        # execute sql
        results = self.session.scalars(sql).all()

        if commit:
            self.session.commit()

        return results

    def update_multiple_items_with_different_values(
        self,
        filters: FilterPayload | None,
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
            filter_generator = FilterGenerator(model=self.model)
            filter_clause = filter_generator.build_filter(filters)
            sql = sql.where(filter_clause)

        self.session.execute(sql, parameters)

        if commit:
            self.session.commit()

    def delete_multiple_items(
        self,
        filters: FilterPayload,
        commit: bool = True,
        joins: Sequence[InstrumentedAttribute] | None = None,
    ) -> Sequence[ModelType]:
        """
        Delete multiple rows. When deleting multiple rows, the deleted rows are returned.
        """

        sql = delete(self.model)

        # construct where clause
        filter_generator = FilterGenerator(model=self.model)
        filter_clause = filter_generator.build_filter(filters)

        if joins:
            mapper = inspect(self.model)
            if mapper is None:
                raise ValueError(f"Model {self.model} is not mapped")

            pks = mapper.primary_key

            subquery = select(*pks).select_from(self.model)

            for join in joins:
                subquery = subquery.join(join)

            subquery = subquery.where(filter_clause)

            if len(pks) > 1:
                sql = sql.where(tuple_(*pks).in_(subquery))
            else:
                sql = sql.where(pks[0].in_(subquery))
        else:
            sql = sql.where(filter_clause)

        sql = sql.returning(self.model)

        # execute sql
        results = self.session.scalars(sql).all()

        if commit:
            self.session.commit()

        return results
