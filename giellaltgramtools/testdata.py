# -*- coding:utf-8 -*-

# Copyright © 2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from dataclasses import dataclass, field

from giellaltgramtools.errordata import ErrorData


@dataclass
class TestData:
    uncorrected: str
    filename: str
    expected_errors: list[ErrorData] = field(default_factory=list)
    gramcheck_errors: list[ErrorData] = field(default_factory=list)
