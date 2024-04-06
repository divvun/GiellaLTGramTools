# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from giellaltgramtools.alloutput import AllOutput


class NoOutput(AllOutput):
    def final_result(self, *args):
        pass
