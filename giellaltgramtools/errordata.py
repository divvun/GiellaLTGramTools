# -*- coding:utf-8 -*-

# Copyright © 2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from dataclasses import dataclass, field


@dataclass
class ErrorData:
    error_string: str
    start: int
    end: int | None
    error_type: str
    explanation: str
    suggestions: list[str] = field(default_factory=list)
    native_error_type: str | None = None
