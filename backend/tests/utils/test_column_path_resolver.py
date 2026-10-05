import json
import pytest
from app.utils.filter_generator import FilterGenerator
from app.models.model import Permission
from sqlalchemy import Function
from sqlalchemy.orm.attributes import InstrumentedAttribute
from app.schemas.filter_generator import FilterPayload
from app.utils.column_path_resolver import ColumnPathResolver


@pytest.mark.parametrize(
    "model, column, expected_attribute",
    [
        pytest.param(
            Permission,
            "role_permissions.created_at",
            "RolePermission.created_at",
            id="role_permissions.created_at",
        )
    ],
)
def test_resolve_attr_path(model, column, expected_attribute):
    """
    Test ColumnPathResolver.resolve_attr_path

    GIVEN a model and a column name
    WHEN calling ColumnPathResolver.resolve_attr_path
    THEN return the built attribute path for the model.column
    """
    model_attribute_utils = ColumnPathResolver(model=model)
    attr = model_attribute_utils.resolve_attr_path(column)

    assert isinstance(attr, InstrumentedAttribute)
    assert str(attr) == expected_attribute


@pytest.mark.parametrize(
    "model, column, expected_instance, expected_attribute",
    [
        pytest.param(
            Permission,
            "action",
            InstrumentedAttribute,
            "Permission.action",
            id="action",
        ),
        # pytest.param(
        #     Permission,
        #     "role_permissions.created_at->some_key",
        #     Function,
        #     'JSON_VALUE("RolePermissions"."created_at", :JSON_VALUE_1)',
        # ), # add a JSON test once we have a JSON column
        pytest.param(
            Permission,
            "role_permissions.created_at",
            InstrumentedAttribute,
            "RolePermission.created_at",
            id="role_permissions.created_at",
        ),
    ],
)
def test_parse_column_to_attribute(
    model, column, expected_instance, expected_attribute
):
    """
    Test ColumnPathResolver.parse_col_to_attr

    GIVEN a model and a column name
    WHEN calling ColumnPathResolver.parse_col_to_attr
    THEN return the built attribute of the correct instance type
    """
    model_attribute_utils = ColumnPathResolver(model=model)
    attr = model_attribute_utils.parse_col_to_attr(column)

    assert isinstance(attr, expected_instance)
    assert str(attr) == expected_attribute
