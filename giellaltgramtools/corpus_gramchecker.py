# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

import sys
from pathlib import Path
from typing import Iterable

from lxml.etree import _Element

from giellaltgramtools.common import get_pipespecs
from giellaltgramtools.gramchecker import GramChecker, check_paragraphs_in_parallel
from giellaltgramtools.testdata import TestData


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

        if not self.config.get("variants"):
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

    def make_test_results(
        self, tests: Iterable[_Element], filename: str
    ) -> Iterable[TestData]:
        error_datas = [self.paragraph_to_testdata(test) for test in tests]
        result_str = check_paragraphs_in_parallel(
            self.checker, [error_data[0] for error_data in error_datas]
        )
        grammar_datas = self.fix_paragraphs(result_str)
        for item in zip(error_datas, grammar_datas, strict=True):
            test_sentence = item[0][0]
            gramcheck_sentence = item[1][0]
            if test_sentence != gramcheck_sentence:
                print(
                    "ERROR: GramDivvun has changed test sentence.\n"
                    f"'{test_sentence}' -> Input to GramDivvun\n"
                    f"'{gramcheck_sentence}' -> Output from GramDivvun\n",
                    f"{filename}\n"
                    "Tip: Check the test sentence using the grammar checker modes.",
                    file=sys.stderr,
                )
                sys.exit(99)  # exit code 99 signals hard exit to Make

        return (
            self.clean_data(
                sentence=item[0][0],
                expected_errors=item[0][1],
                gramcheck_errors=item[1][1],
                filename=filename,
            )
            for item in zip(error_datas, grammar_datas, strict=True)
        )
