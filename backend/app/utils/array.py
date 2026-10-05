from collections.abc import Sequence
from itertools import batched


def chunk_list[T](lst: Sequence[T], chunk_size: int) -> list[tuple[T, ...]]:
    """Split lst into successive chunk_size-sized chunks."""
    return list(batched(lst, chunk_size, strict=False))
