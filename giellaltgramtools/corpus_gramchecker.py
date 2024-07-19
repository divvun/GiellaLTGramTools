# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

import sys
from pathlib import Path

from giellaltgramtools.common import get_pipespecs
from giellaltgramtools.gramchecker import GramChecker


class CorpusGramChecker(GramChecker):
    """Check for grammarerrors in errormarkup files from a Giella corpus."""

    def __init__(self, config):
        super().__init__(config.get("ignore_typos"))
        self.config = config
        self.checker = self.app()

    @staticmethod
    def print_error(string):
        print(string, file=sys.stderr)

    def get_variant(self, spec_file: Path):
        (default_pipe, available_variants) = get_pipespecs(spec_file)

        if self.config.get("variants") is None:
            return f"--variant {default_pipe}"

        variants = {
            variant.replace("-dev", "") if spec_file.suffix == ".zcheck" else variant
            for variant in self.config.get("variants")
        }
        for variant in variants:
            if variant in available_variants:
                return f"--variant {variant}"

        self.print_error(
            "Error in section Variant of the yaml file.\n"
            "There is no pipeline named "
            f"{variant} in {spec_file}"
        )
        available_names = "\n".join(available_variants)
        self.print_error("Available pipelines are\n" f"{available_names}")

        raise SystemExit(5)

    def app(self):
        spec_file = self.config.get("spec")

        checker_spec = (
            f"--archive {spec_file}"
            if spec_file.suffix == ".zcheck"
            else f"--spec {spec_file}"
        )

        return f"divvun-checker {checker_spec} {self.get_variant(spec_file)}"
