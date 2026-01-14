from typing import Iterable

from giellaltgramtools.errordata import ErrorData

ErrorDatas = tuple[ErrorData, ...]

def sort_by_range(errors: Iterable[ErrorData]) -> ErrorDatas:
    """Sort error data by their range in the text.

    Args:
        errors (Iterable[ErrorData]): List of error data to sort.
    Returns:
        ErrorDatas sorted by their start and end positions.
    """
    return tuple(sorted(errors, key=lambda error: (error.start, error.end)))

