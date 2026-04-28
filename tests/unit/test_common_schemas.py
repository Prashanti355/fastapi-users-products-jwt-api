import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

from app.schemas.common import (
    PagedResult,
    PaginationParams,
    SearchParams,
    SortingParams,
    SortOrder,
)


class DummyItemSchema(BaseModel):
    value: int

    model_config = ConfigDict(from_attributes=True)


class DummyItem:
    def __init__(self, value: int):
        self.value = value


def test_sort_order_enum_values():
    assert SortOrder.ASC.value == "asc"
    assert SortOrder.DESC.value == "desc"


def test_pagination_params_defaults():
    params = PaginationParams()

    assert params.page == 1
    assert params.limit == 10


def test_pagination_params_accepts_valid_values():
    params = PaginationParams(page=3, limit=25)

    assert params.page == 3
    assert params.limit == 25


def test_pagination_params_rejects_invalid_page():
    with pytest.raises(ValidationError):
        PaginationParams(page=0, limit=10)


def test_pagination_params_rejects_invalid_limit_below_range():
    with pytest.raises(ValidationError):
        PaginationParams(page=1, limit=0)


def test_pagination_params_rejects_invalid_limit_above_range():
    with pytest.raises(ValidationError):
        PaginationParams(page=1, limit=101)


def test_sorting_params_defaults():
    params = SortingParams()

    assert params.sort_by == "created_at"
    assert params.order == SortOrder.DESC


def test_sorting_params_accepts_custom_values():
    params = SortingParams(sort_by="username", order=SortOrder.ASC)

    assert params.sort_by == "username"
    assert params.order == SortOrder.ASC


def test_search_params_defaults():
    params = SearchParams()

    assert params.search is None
    assert params.is_active is None


def test_search_params_accepts_values():
    params = SearchParams(search="maya", is_active=True)

    assert params.search == "maya"
    assert params.is_active is True


def test_paged_result_accepts_typed_list_data():
    result = PagedResult[int](
        total=3,
        page=1,
        limit=10,
        data=[1, 2, 3],
    )

    assert result.total == 3
    assert result.page == 1
    assert result.limit == 10
    assert result.data == [1, 2, 3]


def test_paged_result_supports_from_attributes():
    item = DummyItem(value=42)

    validated = PagedResult[DummyItemSchema].model_validate(
        {
            "total": 1,
            "page": 1,
            "limit": 10,
            "data": [item],
        },
        from_attributes=True,
    )

    assert validated.total == 1
    assert validated.page == 1
    assert validated.limit == 10
    assert validated.data[0].value == 42
