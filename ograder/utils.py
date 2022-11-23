import itertools
from typing import Any

def peek(iterable) -> Any:
    try:
        first = next(iterable)
    except StopIteration:
        return None
    return first, itertools.chain([first], iterable)