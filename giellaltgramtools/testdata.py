# Copyright © 2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from __future__ import annotations

from dataclasses import dataclass

from giellaltgramtools.errordata import ErrorData


@dataclass
class TestData:
    uncorrected: str
    filename: str
    expected_errors: tuple[ErrorData, ...]
    gramcheck_errors: tuple[ErrorData, ...]