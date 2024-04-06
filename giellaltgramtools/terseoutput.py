# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from giellaltgramtools.alloutput import AllOutput
from giellaltgramtools.common import colourise


class TerseOutput(AllOutput):
    def success(self, *args):
        self.write(colourise("{green}.{reset}"))

    def failure(self, *args):
        self.write(colourise("{red}!{reset}"))

    def result(self, *args):
        self.write("\n")

    def final_result(self, count):
        fails = sum([count[key] for key in count if key != "tp"])
        if fails:
            self.write(colourise("{red}FAIL{reset}\n"))
        else:
            self.write(colourise("{green}PASS{reset}\n"))
