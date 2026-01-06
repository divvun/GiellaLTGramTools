# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from io import StringIO

from giellaltgramtools.common import colourise


class AllOutput:
    def __init__(self):
        self._io = StringIO()

    def __str__(self):
        return self._io.getvalue()

    def write(self, data):
        self._io.write(data)

    def info(self, data):
        self.write(data)

    def title(self, *args):
        pass

    def success(self, *args):
        pass

    def failure(self, *args):
        pass

    def false_positive_1(self, *args):
        pass

    def result(self, *args):
        pass

    def final_result(self, count):
        passes = count["tp"]
        fails = sum([count[key] for key in count if key != "tp"])
        self.write(
            colourise(
                "Total passes: {green}{passes}{reset}, "
                + "Total fails: {red}{fails}{reset}, "
                + "Total: {light_blue}{total}{reset}\n",
                passes=passes,
                fails=fails,
                total=fails + passes,
            )
        )
