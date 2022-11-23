import itertools
from typing import Any

def peek(iterable) -> Any:
    try:
        first = next(iterable)
    except StopIteration:
        return None, None
    return first, itertools.chain([first], iterable)

def is_empty(iterable) -> bool:
    element, _ =  peek(iterable)
    return element == None