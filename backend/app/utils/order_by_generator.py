from typing import Any, Generic, Type, TypeVar
from sqlalchemy import UnaryExpression
from app.utils.model import ModelAttributeUtils
from app.schemas.order_by_generator import OrderByCondition, OrderOperator
from sqlalchemy.sql.elements import KeyedColumnElement

ModelType = TypeVar("ModelType")
Schema = TypeVar("Schema")


class ParamToOrderByConditionConfig:
    def __init__(
        self, condition_separator: str = ":", item_separator: str = ","
    ) -> None:
        self.condition_separator = condition_separator
        self.item_separator = item_separator


def parse_param_to_order_by_condition(
    param: str,
    config: ParamToOrderByConditionConfig = ParamToOrderByConditionConfig(
        condition_separator=":", item_separator=","
    ),
) -> list[OrderByCondition]:

    order_items = param.split(config.item_separator)

    order_state = [
        OrderByCondition(
            column=item_parts[0],
            orientation=(
                OrderOperator.asc_ if item_parts[1] == "asc" else OrderOperator.desc_
            ),
        )
        for order_item in order_items
        if (item_parts := order_item.split(config.condition_separator))
    ]

    return order_state


class OrderByGenerator(Generic[ModelType, Schema]):

    def __init__(
        self,
        model: Type[ModelType],
        column_mapping: dict[str, KeyedColumnElement] = {},
    ) -> None:
        self.model = model
        self.model_attribute_utils = ModelAttributeUtils(model=model)
        self.column_mapping = column_mapping

    def build_order_conditional(self, conditions: list[OrderByCondition]):
        operators: list[UnaryExpression[Any]] = []
        for condition in conditions:
            attr = (
                self.column_mapping.get(condition.column, None)
                if self.column_mapping.get(condition.column, None) is not None
                else self.model_attribute_utils.parse_column_to_attribute(
                    condition.column
                )
            )
            if attr is None:
                raise Exception("Attribute could not be mapped")

            match condition.orientation:
                case OrderOperator.asc_:
                    operators.append(attr.asc())
                case OrderOperator.desc_:
                    operators.append(attr.desc())
                case _:
                    operators.append(attr.asc())

        return operators
