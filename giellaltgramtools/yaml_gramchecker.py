# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
import sys
from pathlib import Path
from typing import Iterator

from corpustools.error_annotated_sentence import (
    ErrorAnnotatedSentence,
    parse_markup_to_sentence,
)

from giellaltgramtools.common import get_pipespecs
from giellaltgramtools.errordata import ErrorData
from giellaltgramtools.gramchecker import (
    GramChecker,
    check_paragraphs_in_parallel,
)
from giellaltgramtools.testdata import TestData


class YamlGramChecker(GramChecker):
    def __init__(self, config):
        super().__init__()
        self.config = config
        # Check if runtime should be used
        self.use_runtime = config.get("use_runtime", False)
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

        # Check if we should use divvun-runtime
        if self.use_runtime:
            # Use divvun-runtime with bundle.drb
            # Default to ../bundle.drb relative to the spec file location
            if spec_file:
                bundle_path = Path(spec_file).parent / "bundle.drb"
            else:
                # Fallback if no spec file provided
                bundle_path = Path("bundle.drb")
            
            # Get variant from config
            variant = self.config.get("variant")
            
            # Map smegram-dev variant to sme-gram pipeline
            if variant == "smegram-dev":
                return f"divvun-runtime run -p {bundle_path} -P sme-gram"
            elif variant:
                return f"divvun-runtime run -p {bundle_path} -P {variant}"
            else:
                return f"divvun-runtime run -p {bundle_path}"
        
        # Use divvun-checker (default)
        checker_spec = (
            f"--archive {spec_file}"
            if spec_file.suffix == ".zcheck"
            else f"--spec {spec_file}"
        )

        return f"divvun-checker {checker_spec} {self.get_variant(spec_file)}"

    def make_test_results(self, tests: list[str]) -> Iterator[TestData]:
        error_annotated_sentences: list[ErrorAnnotatedSentence] = [
            parse_markup_to_sentence(text)
            for text in tests
            if text.strip()
        ]
        
        error_datas = [
            (error_annotated_sentence.text, [
                ErrorData(
                    error_string=error.form_as_string(),
                    start=error.start,
                    end=error.end,
                    error_type=error.errortype.name.lower(),
                    explanation=error.errorinfo,
                    suggestions=error.suggestions,
                    native_error_type='',
                )
                for error in error_annotated_sentence.errors
            ])
            for error_annotated_sentence in error_annotated_sentences]

        # Use the same function regardless of checker type
        # The conversion happens automatically inside check_paragraphs_in_parallel
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
