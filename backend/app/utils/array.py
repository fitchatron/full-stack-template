from itertools import batched
from typing import Any


def chunk_list(lst: list[Any], chunk_size: int):
    """Yield successive n-sized chunks from lst."""
    return list(batched(lst, chunk_size))
