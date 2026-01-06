# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
import re
import sys
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Iterable

import click
import yaml
from yaml import FullLoader, load

from giellaltgramtools.common import COLORS
from giellaltgramtools.finaloutput import FinalOutput
from giellaltgramtools.gramtest import GramTest
from giellaltgramtools.nooutput import NoOutput
from giellaltgramtools.normaloutput import NormalOutput
from giellaltgramtools.testdata import TestData
from giellaltgramtools.yaml_config import YamlConfig
from giellaltgramtools.yaml_gramchecker import YamlGramChecker
from giellaltgramtools.yaml_test_file import load_yaml_file


class YamlGramTest(GramTest):
    explanations = {
        "tp": "GramDivvun found marked up error and has the suggested correction",
        "fp1": "GramDivvun found manually marked up error, but corrected wrongly",
        "fp2": "GramDivvun found error which is not manually marked up",
        "fn1": "GramDivvun found manually marked up error, but has no correction",
        "fn2": "GramDivvun did not find manually marked up error",
    }

    def __init__(self, ctx: click.Context, filename: Path) -> None:
        super().__init__()
        self.config: YamlConfig = self.load_config(ctx, filename)

    def load_config(self, ctx: click.Context, filename: Path) -> YamlConfig:
        if not ctx.obj.get("colour"):
            for key in list(COLORS.keys()):
                COLORS[key] = ""

        yaml_content = load_yaml_file(filename)

        if ctx.obj.get("remove_dupes", False):
            self.remove_dupes(filename, yaml_content.tests)

        yaml_config = YamlConfig(
            output=NoOutput()
            if ctx.obj.get("output") == "silent"
            else (FinalOutput() if ctx.obj["output"] == "final" else NormalOutput()),
            hide_passes=ctx.obj["hide_passes"],
            move_tests=ctx.obj["move_tests"],
            spec=yaml_content.spec
            if ctx.obj["spec"] is None
            else Path(ctx.obj["spec"]),
            variant=yaml_content.variant
            if ctx.obj["variant"] is None
            else ctx.obj["variant"],
            tests=yaml_content.tests,
            test_file=filename,
            use_runtime=ctx.obj.get("use_runtime", False    )
        )

        return yaml_config

    def _get_duplicate_tests(
        self, tests: list[str]
    ) -> tuple[set[tuple[str, int]], Counter[str]]:
        """Identify duplicate tests and return them."""
        counted_tests = Counter(tests)
        return {
            counted_test
            for counted_test in counted_tests.items()
            if counted_test[1] > 1
        }, counted_tests

    def _process_test_line(self, line, test_re, counted_tests, temp_stream):
        """Process a single line from the test file."""
        match = test_re.search(line.rstrip())
        if not match:
            temp_stream.write(line)
            return

        test_string = match.group("test")[1:-1]
        if match and match.group("test"):
            if counted_tests.get(test_string) > 1:
                counted_tests[test_string] -= 1
            else:
                temp_stream.write(line)

    def _write_deduplicated_file(self, test_file: Path, counted_tests):
        """Write the file without duplicates."""
        test_re = re.compile(
            r"""^(\s*-\s+)(?P<test>("[^"]+"|'[^']+')).*$""", re.UNICODE
        )

        with StringIO() as temp_stream:
            for line in test_file.read_text().splitlines(keepends=True):
                self._process_test_line(line, test_re, counted_tests, temp_stream)
            test_file.write_text(temp_stream.getvalue())

    def remove_dupes(self, test_file: Path, tests: list[str]) -> None:
        """Remove duplicate tests from the test file"""
        dupes, counted_tests = self._get_duplicate_tests(tests)

        if dupes:  # remove duplicates
            self._write_deduplicated_file(test_file, counted_tests)

            print(
                f"ERROR: Removed the following dupes in {test_file}\n\n".join(
                    "\t" + dupe[0] for dupe in dupes
                ),
                file=sys.stderr,
            )
            sys.exit(99)  # exit code 99 signals hard exit to Make

    @staticmethod
    def yaml_reader(test_file):
        with test_file.open() as test_file_stream:
            return load(test_file_stream, Loader=FullLoader)

    def make_test_results(self) -> Iterable[TestData]:
        if not self.config.tests:
            return []

        grammarchecker = YamlGramChecker(self.config)
        return grammarchecker.make_test_results(self.config.tests)

    def move_passes_from_fail(self) -> None:
        if "FAIL" in self.config.test_file.name and any(self.test_outcomes):
            passing_tests = [
                self.config.tests[index]
                for (index, test_result) in enumerate(self.test_outcomes)
                if test_result
            ]

            pass_path = Path(str(self.config.test_file).replace("FAIL", "PASS"))
            if not pass_path.exists():
                pass_data = self.yaml_reader(self.config.test_file)
                del pass_data["Tests"]
                pass_path.write_text(yaml.dump(pass_data) + "\nTests:\n")

            with pass_path.open("a") as pass_stream:
                for this_test in passing_tests:
                    quote_mark = "'" if '"' in this_test else '"'
                    print(f"  - {quote_mark}{this_test}{quote_mark}", file=pass_stream)

            with StringIO() as temp_stream:
                with self.config.test_file.open("r") as _input:
                    temp_stream.write(
                        "".join(
                            [
                                line
                                for line in _input
                                if not any(
                                    passing_test in line.strip()
                                    for passing_test in passing_tests
                                )
                            ]
                        )
                    )
                self.config.test_file.open("w").write(temp_stream.getvalue())

    def move_fails_from_pass(self) -> None:
        if "PASS" in self.config.test_file.name and any(self.test_outcomes):
            failing_tests = [
                self.config.tests[index]
                for (index, test_result) in enumerate(self.test_outcomes)
                if not test_result
            ]

            fail_path = Path(str(self.config.test_file).replace("PASS", "FAIL"))
            if not fail_path.exists():
                fail_data = self.yaml_reader(self.config.test_file)
                del fail_data["Tests"]
                fail_path.write_text(yaml.dump(fail_data) + "\nTests:\n")
            with fail_path.open("a") as fail_stream:
                for this_test in failing_tests:
                    quote_mark = "'" if '"' in this_test else '"'
                    print(f"  - {quote_mark}{this_test}{quote_mark}", file=fail_stream)
            with StringIO() as temp_stream:
                with self.config.test_file.open("r") as _input:
                    temp_stream.write(
                        "".join(
                            [
                                line
                                for line in _input
                                if not any(
                                    failing_test in line.strip()
                                    for failing_test in failing_tests
                                )
                            ]
                        )
                    )
                self.config.test_file.open("w").write(temp_stream.getvalue())

    def run(self) -> int:
        failed_or_not = super().run()

        if self.config.move_tests:
            self.move_passes_from_fail()
            self.move_fails_from_pass()

        return failed_or_not
