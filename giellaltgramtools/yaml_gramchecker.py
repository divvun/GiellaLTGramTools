# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
import sys
from pathlib import Path
from typing import Iterator

from corpustools.error_annotated_sentence import (
    parse_markup_to_sentence,
)

from giellaltgramtools.common import get_pipespecs
from giellaltgramtools.gramchecker import (
    GramChecker,
    check_paragraphs_in_parallel,
)
from giellaltgramtools.grammar_error_annotated_sentence import (
    GrammarErrorAnnotatedSentence,
    error_annotated_sentence_to_grammar_error_annotated_sentence,
)
from giellaltgramtools.testdata import TestData
from giellaltgramtools.yaml_config import YamlConfig


class GramCheckerSentenceError(Exception):
    """Exception for errors in grammar checker sentence processing."""

    pass


class YamlGramChecker(GramChecker):
    def __init__(self, config: YamlConfig):
        super().__init__()
        self.config = config
        # Check if runtime should be used
        self.use_runtime = config.use_runtime
        self.checker = self.app()

    @staticmethod
    def print_error(string):
        print(string, file=sys.stderr)

    def get_variant(self, spec_file: Path):
        (default_pipe, available_variants) = get_pipespecs(spec_file)

        if self.config.variant is None:
            return f"--variant {default_pipe}"

        variant = (
            self.config.variant.replace("-dev", "")
            if spec_file.suffix == ".zcheck"
            else self.config.variant
        )
        if variant in available_variants:
            return f"--variant {variant}"

        self.print_error(
            "Error in section Variant of the yaml file.\n"
            "There is no pipeline named "
            f"{variant} in {spec_file}"
        )
        available_names = "\n".join(available_variants)
        self.print_error(f"Available pipelines are\n{available_names}")

        raise SystemExit(5)

    def app(self):
        spec_file = self.config.spec

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
            variant = self.config.variant

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

    def make_error_datas(self) -> Iterator[GrammarErrorAnnotatedSentence]:
        """Make GrammarErrorAnnotatedSentence from the test sentences."""
        for index, text in enumerate(self.config.tests):
            if text.strip():
                modified_text = f"{text}." if text[-1] not in ".!?" else text
                try:
                    error_annotated_sentence = parse_markup_to_sentence(
                        iter(modified_text)
                    )
                except ValueError as error:
                    self.print_error(
                        f"Error parsing test sentence {index + 1}\n{text} in "
                        f"{self.config.test_file}:\n{error}"
                    )
                    raise SystemExit(4) from error
                yield error_annotated_sentence_to_grammar_error_annotated_sentence(
                    error_annotated_sentence
                )

    def make_test_results(self, tests: list[str]) -> Iterator[TestData]:
        error_datas: list[GrammarErrorAnnotatedSentence] = list(self.make_error_datas())

        grammar_datas = check_paragraphs_in_parallel(
            self.checker, [error_data.sentence for error_data in error_datas]
        )

        for item in zip(error_datas, grammar_datas, strict=True):
            test_sentence = item[0].sentence
            gramcheck_sentence = item[1].sentence
            if test_sentence != gramcheck_sentence:
                raise GramCheckerSentenceError(
                    "ERROR: GramDivvun has changed test sentence.\n"
                    f"'{test_sentence}' -> Input to GramDivvun\n"
                    f"'{gramcheck_sentence}' -> Output from GramDivvun\n",
                    "Tip: Check the test sentence using the grammar checker modes.",
                )

        return (
            self.clean_data(
                sentence=item[0].sentence,
                expected_errors=item[0].errors,
                gramcheck_errors=item[1].errors,
                filename=self.config.test_file.name,
            )
            for item in zip(error_datas, grammar_datas, strict=True)
        )
