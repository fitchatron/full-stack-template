import pytest
from app.utils.array import chunk_list


@pytest.mark.parametrize(
    "list, size, expected",
    [
        pytest.param(
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            3,
            [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9,)],
            id="chunk_list_with_size_3",
        ),
        pytest.param(
            [
                "hello",
                "there",
                "foo",
                "bar",
                "foobar",
                "fisbuzz",
                "baz",
                "qux",
                "lorem",
                "ipsum",
                "",
            ],
            3,
            [
                ("hello", "there", "foo"),
                ("bar", "foobar", "fisbuzz"),
                ("baz", "qux", "lorem"),
                ("ipsum", ""),
            ],
            id="chunk_str_list_with_size_3",
        ),
        pytest.param(
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            4,
            [(0, 1, 2, 3), (4, 5, 6, 7), (8, 9)],
            id="chunk_list_with_size_4",
        ),
        pytest.param(
            [1],
            1,
            [(1,)],
            id="chunk_list_with_size_1_single_element",
        ),
        pytest.param(
            [1],
            2,
            [(1,)],
            id="chunk_list_with_size_2_single_element",
        ),
        pytest.param(
            [],
            1,
            [],
            id="chunk_list_with_empty_list",
        ),
    ],
)
def test_chunk_list(list: list[int | str], size: int, expected: list[list[int | str]]):
    assert chunk_list(list, size) == expected


def test_chunk_list_with_negative_size():
    with pytest.raises(
        ValueError,
        match=r"n must be at least one",
    ):
        chunk_list([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], -1)
