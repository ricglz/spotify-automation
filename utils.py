'''
Collection of utility functions
'''
from typing import Iterable, Iterator, List, TypeVar

T = TypeVar('T')

def create_chunks(iterable: Iterable[T], chunk_size: int) -> Iterator[List[T]]:
    """
    Generate several lists of size `chunk_size` based on the elements in the
    given `arr` list.
    """
    iterator = iter(iterable)
    while True:
        try:
            temp: List[T] = [next(iterator)]
        except StopIteration:
            break
        try:
            for _ in range(chunk_size - 1):
                temp.append(next(iterator))
        except StopIteration:
            yield temp
            break
        yield temp
