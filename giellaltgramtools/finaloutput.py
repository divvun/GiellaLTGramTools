# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from giellaltgramtools.alloutput import AllOutput


class FinalOutput(AllOutput):
    def final_result(self, count):
        passes = sum([count[key] for key in count if key.startswith("t")])
        fails = sum([count[key] for key in count if key.startswith("f")])
        self.write(f"{passes}/{fails}/{passes+fails}")
