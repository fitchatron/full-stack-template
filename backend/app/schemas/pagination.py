from typing import TypeVar

from fastapi_pagination.customization import CustomizedPage, UseOptionalParams
from fastapi_pagination.links import Page

T = TypeVar("T")

OptionalPage = CustomizedPage[Page[T], UseOptionalParams()]
