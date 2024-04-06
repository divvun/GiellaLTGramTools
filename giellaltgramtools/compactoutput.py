# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from giellaltgramtools.alloutput import AllOutput
from giellaltgramtools.common import colourise


class CompactOutput(AllOutput):
    def result(self, number, count, test_case):
        passes = sum([count[key] for key in count if key.startswith("t")])
        fails = sum([count[key] for key in count if key.startswith("f")])
        out = f"{test_case} {passes}/{fails}/{passes + fails}"
        if fails:
            self.write(colourise("[{red}FAIL{reset}] {}\n", out))
        else:
            self.write(colourise("[{green}PASS{reset}] {}\n", out))
