# Copyright © 2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from corpustools.error_annotated_sentence import ErrorMarkup


@dataclass
class ErrorData:
    error_string: str
    start: int
    end: int
    error_type: str
    explanation: str
    suggestions: list[str] = field(default_factory=list)


def error_markup_to_error_data(error_markup: ErrorMarkup, offset: int = 0) -> ErrorData:
    """Convert an ErrorMarkup to ErrorData.

    Args:
        error_markup (ErrorMarkup): The ErrorMarkup to convert.
        offset (int): Offset to add to start and end positions.
    Returns:
        ErrorData: The converted ErrorData object.
    """
    error_string = error_markup.uncorrected_text()
    error_data = ErrorData(
        error_string=error_string,
        start=offset,
        end=offset + len(error_string),
        error_type=str(error_markup.errortype),
        explanation=error_markup.correction.error_info
        if error_markup.correction.error_info is not None
        else "",
        suggestions=error_markup.correction.suggestions,
    )

    return error_data


def divvun_checker_to_error_data(
    divvun_checker_error: tuple,
) -> ErrorData:
    """Convert a divvun-checker error tuple to ErrorData.
    Args:
        divvun_checker_error (tuple): A tuple representing a divvun-checker
    Returns:
        ErrorData: The converted ErrorData object.
    """
    return ErrorData(
        error_string=divvun_checker_error[0],
        start=divvun_checker_error[1],
        end=divvun_checker_error[2],
        error_type=divvun_checker_error[3],
        explanation=divvun_checker_error[4],
        suggestions=divvun_checker_error[5],
    )


def fix_aistton_both(aistton_both: ErrorData) -> Iterator[ErrorData]:
    """Split grammar checker punct-aistton-both error into two separate errors.

    Args:
        aistton_both (ErrorData): The original error data representing both errors.

    Yields:
        Two separate ErrorData that mimics the manual error markup.
    """
    yield ErrorData(
        error_string=aistton_both.error_string[0],
        start=aistton_both.start,
        end=aistton_both.start + 1,
        error_type=aistton_both.error_type,
        explanation=aistton_both.explanation,
        suggestions=[aistton_both.suggestions[0][0]],
    )
    yield ErrorData(
        error_string=aistton_both.error_string[-1],
        start=aistton_both.end - 1,
        end=aistton_both.end,
        error_type=aistton_both.error_type,
        explanation=aistton_both.explanation,
        suggestions=[aistton_both.suggestions[-1][-1]],
    )


def fix_aistton_right(aistton_right: ErrorData) -> ErrorData:
    """Fix grammar checker punct-aistton-right error to match manual error markup.

    Args:
        The original error data representing the right aistton error.
    Returns:
        Fixed ErrorData that mimics the manual error markup.
    """
    return ErrorData(
        error_string=aistton_right.error_string[-1],
        start=aistton_right.end - 1,
        end=aistton_right.end,
        error_type=aistton_right.error_type,
        explanation=aistton_right.explanation,
        suggestions=[aistton_right.suggestions[0][-1]],
    )


def fix_aistton_left(aistton_left: ErrorData) -> ErrorData:
    """Fix grammar checker punct-aistton-left error to match manual error markup.

    Args:
        The original error data representing the left aistton error.
    Returns:
        Fixed ErrorData that mimics the manual error markup.
    """
    return ErrorData(
        error_string=aistton_left.error_string[0],
        start=aistton_left.start,
        end=aistton_left.start + 1,
        error_type=aistton_left.error_type,
        explanation=aistton_left.explanation,
        suggestions=[aistton_left.suggestions[0][0]],
    )


def remove_aistton(errors: list[ErrorData]) -> list[ErrorData]:
    """Remove punct-aistton errors from the list of error data.

    Args:
        errors (list[ErrorData]): The original list of error data
    Returns:
        List of ErrorData with punct-aistton errors removed.
    """
    return [error for error in errors if not error.error_type == "punct-aistton"]
