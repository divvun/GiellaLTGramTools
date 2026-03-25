# -*- coding:utf-8 -*-

# Copyright © 2020-2026 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
import sys
from pathlib import Path

from giellaltgramtools.common import get_pipespecs
from giellaltgramtools.gramchecker import (
    GramChecker,
    GramCheckerSentenceError,
)
from giellaltgramtools.grammar_error_annotated_sentence import (
    GrammarErrorAnnotatedSentence,
)
from giellaltgramtools.yaml_config import YamlConfig


def check_if_grammarchecker_changed_input(
    error_datas: list[GrammarErrorAnnotatedSentence],
    grammar_datas: list[GrammarErrorAnnotatedSentence],
) -> None:
    """Check if grammar checker has changed the input sentences.

    Args:
        error_datas: List of GrammarErrorAnnotatedSentence from test data.
        grammar_datas: List of GrammarErrorAnnotatedSentence from grammar checker.
    Raises:
        GramCheckerSentenceError: If grammar checker has changed any input sentence.
    """
    differing_sentences: list[tuple[str, str]] = [
        (item[0].sentence, item[1].sentence)
        for item in zip(error_datas, grammar_datas, strict=True)
        if item[0].sentence != item[1].sentence
    ]
    if differing_sentences:
        for test_sentence, gramcheck_sentence in differing_sentences:
            error_messages = (
                f"'{test_sentence}' -> Input to GramDivvun\n"
                f"'{gramcheck_sentence}' -> Output from GramDivvun\n"
            )
            raise GramCheckerSentenceError(
                f"ERROR: GramDivvun has changed test sentences.\n{error_messages}",
                "Tip: Check the test sentences using the grammar checker modes.",
            )


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
