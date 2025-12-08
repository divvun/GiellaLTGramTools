# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
import sys
from pathlib import Path
from typing import Iterator

from corpustools import errormarkup  # type: ignore
from lxml.etree import Element, _Element

from giellaltgramtools.common import get_pipespecs
from giellaltgramtools.gramchecker import (
    GramChecker,
    check_paragraphs_in_parallel,
    check_paragraphs_with_runtime_parallel,
)
from giellaltgramtools.testdata import TestData


class YamlGramChecker(GramChecker):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.use_runtime = config.get("use_runtime", False)
        self.checker = self.app()

    @staticmethod
    def print_error(string):
        print(string, file=sys.stderr)

    def make_error_markup(self, text: str) -> _Element:
        para: _Element = Element("p")
        try:
            para.text = text
            errormarkup.convert_to_errormarkupxml(para)
        except TypeError:
            print(f'Error in {self.config["test_file"]}')
            print(text, "is not a string")
        return para

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

        # Check if we should use divvun-runtime
        if self.use_runtime:
            # Use divvun-runtime with .drb bundle or .ts pipeline
            if spec_file.suffix not in [".drb", ".ts"]:
                self.print_error(
                    f"Error: --use-runtime requires a .drb or .ts file, got {spec_file.suffix}"
                )
                raise SystemExit(5)
            return f"divvun-runtime run -p {spec_file}"
        
        # Use divvun-checker (default)
        checker_spec = (
            f"--archive {spec_file}"
            if spec_file.suffix == ".zcheck"
            else f"--spec {spec_file}"
        )

        return f"divvun-checker {checker_spec} {self.get_variant(spec_file)}"

    def make_test_results(self, tests: list[str]) -> Iterator[TestData]:
        error_datas = [
            self.paragraph_to_testdata(self.make_error_markup(text))
            for text in tests
            if text.strip()
        ]
        
        # Choose checker based on configuration
        if self.use_runtime:
            result_str = check_paragraphs_with_runtime_parallel(
                self.checker, [error_data[0] for error_data in error_datas]
            )
        else:
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
                    "Tip: Check the test sentence using the grammar checker modes.",
                    file=sys.stderr,
                )
                sys.exit(99)  # exit code 99 signals hard exit to Make

        return (
            self.clean_data(
                sentence=item[0][0],
                expected_errors=item[0][1],
                gramcheck_errors=item[1][1],
                filename=self.config["test_file"].name,
            )
            for item in zip(error_datas, grammar_datas, strict=True)
        )
