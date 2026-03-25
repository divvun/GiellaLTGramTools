# -*- coding:utf-8 -*-

# Copyright © 2020-2026 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
import sys

from giellaltgramtools.common import get_pipespecs
from giellaltgramtools.corpus_config import CorpusConfig
from giellaltgramtools.gramchecker import GramChecker


class CorpusGramChecker(GramChecker):
    """Check for grammarerrors in errormarkup files from a Giella corpus."""

    def __init__(self, config: CorpusConfig):
        super().__init__(config.ignore_typos)
        self.config = config
        self.checker = self.app()

    @staticmethod
    def print_error(string: str) -> None:
        print(string, file=sys.stderr)

    def get_variant(self) -> str:
        (default_pipe, available_variants) = get_pipespecs(self.config.spec)

        if not self.config.variant:
            return f"--variant {default_pipe}"

        variants = {
            self.config.variant.replace("-dev", "")
            if self.config.spec.suffix == ".zcheck"
            else self.config.variant
        }
        for variant in variants:
            if variant in available_variants:
                return f"--variant {variant}"

        self.print_error(
            "Error in section Variant of the yaml file.\n"
            "There is no pipeline named "
            f"{variant} in {self.config.spec}"
        )
        available_names = "\n".join(available_variants)
        self.print_error(f"Available pipelines are\n{available_names}")

        raise SystemExit(5)

    def app(self):
        spec_file = self.config.spec

        checker_spec = (
            f"--archive {spec_file}"
            if spec_file.suffix == ".zcheck"
            else f"--spec {spec_file}"
        )

        return f"divvun-checker {checker_spec} {self.get_variant()}"
