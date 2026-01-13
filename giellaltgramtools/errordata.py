# Copyright © 2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from __future__ import annotations

from dataclasses import dataclass, field

from corpustools.error_annotated_sentence import ErrorMarkup


@dataclass(frozen=True)
class ErrorData:
    error_string: str
    start: int
    end: int
    error_type: str
    explanation: str
    suggestions: tuple[str, ...] = field(default_factory=tuple)


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
        suggestions=tuple(error_markup.correction.suggestions),
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


