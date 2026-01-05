# Copyright © 2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from __future__ import annotations

from dataclasses import dataclass, field

from corpustools.error_annotated_sentence import ErrorMarkup


@dataclass
class ErrorData:
    error_string: str
    start: int
    end: int
    error_type: str
    explanation: str
    suggestions: list[str] = field(default_factory=list)
    native_error_type: str | None = None


def error_markup_to_error_data(error_markup: ErrorMarkup, offset: int = 0) -> ErrorData:
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
