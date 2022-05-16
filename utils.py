'''
Collection of utility functions
'''
from math import ceil
from typing import Iterator, List, TypeVar

T = TypeVar('T')

def create_chunks(arr: List[T], chunk_size: int) -> Iterator[List[T]]:
    """
    Generate several lists of size `chunk_size` based on the elements in the
    given `arr` list.
    """
    number_of_chunks = ceil(len(arr) / chunk_size)
    for chunk in range(number_of_chunks):
        start = chunk * chunk_size
        end = start + chunk_size
        yield arr[start:end]
