# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
import sys
from io import StringIO
from pathlib import Path
from typing import Iterable

import yaml

from giellaltgramtools.common import COLORS
from giellaltgramtools.finaloutput import FinalOutput
from giellaltgramtools.gramtest import GramTest
from giellaltgramtools.nooutput import NoOutput
from giellaltgramtools.normaloutput import NormalOutput
from giellaltgramtools.testdata import TestData
from giellaltgramtools.yaml_gramchecker import YamlGramChecker


class YamlGramTest(GramTest):
    explanations = {
        "tp": "GramDivvun found marked up error and has the suggested correction",
        "fp1": "GramDivvun found manually marked up error, but corrected wrongly",
        "fp2": "GramDivvun found error which is not manually marked up",
        "fn1": "GramDivvun found manually marked up error, but has no correction",
        "fn2": "GramDivvun did not find manually marked up error",
    }

    def __init__(self, args, filename=None):
        super().__init__()
        self.config = self.load_config(args, filename)

    def load_config(self, args, filename):
        output_dict = {
            "normal": NormalOutput,
            "final": FinalOutput,
            "silent": NoOutput,
        }
        config = {}

        config["hide_passes"] = args.get("hide_passes", False)
        config["out"] = output_dict[args.get("output")](args)
        config["test_file"] = filename

        if not args.get("colour"):
            for key in list(COLORS.keys()):
                COLORS[key] = ""

        try:
            yaml_settings = self.yaml_reader(config["test_file"])
        except yaml.parser.ParserError as error:
            print(
                f"ERROR: {config['test_file']} is not a valid YAML file",
                file=sys.stderr,
            )
            print(error, file=sys.stderr)
            sys.exit(99)

        try:
            config["spec"] = (
                config["test_file"].parent / yaml_settings.get("Config").get("Spec")
                if not args.get("spec")
                else Path(args.get("spec"))
            )
        except AttributeError:
            print(
                f"ERROR: No spec in {config['test_file']}",
                file=sys.stderr,
            )
            sys.exit(99)
        config["variants"] = (
            yaml_settings.get("Config").get("Variants")
            if not args.get("variant")
            else [args.get("variant")]
        )
        config["tests"] = yaml_settings.get("Tests", [])

        if not config["tests"]:
            print(
                f"ERROR: No tests in {config['test_file']}",
                file=sys.stderr,
            )
            sys.exit(99)  # exit code 99 signals hard exit to Make
        dupes = "\n".join(
            {f"\t{test}" for test in config["tests"] if config["tests"].count(test) > 1}
        )
        if dupes:  # check for duplicates
            print(
                f"ERROR: Remove the following dupes in {config['test_file']}\n{dupes}",
                file=sys.stderr,
            )
            sys.exit(99)  # exit code 99 signals hard exit to Make

        return config

    @staticmethod
    def yaml_reader(test_file):
        with test_file.open() as test_file_stream:
            return yaml.load(test_file_stream, Loader=yaml.FullLoader)

    def make_test_results(self) -> Iterable[TestData]:
        if not self.config["tests"]:
            return []

        grammarchecker = YamlGramChecker(self.config)
        return grammarchecker.make_test_results(self.config["tests"])

    def move_passes_from_fail(self) -> None:
        if "FAIL" in self.config["test_file"].name and any(self.test_outcomes):
            passing_tests = [
                self.config["tests"][index]
                for (index, test_result) in enumerate(self.test_outcomes)
                if test_result
            ]

            pass_path = Path(str(self.config["test_file"]).replace("FAIL", "PASS"))
            with pass_path.open("a") as pass_stream:
                print(
                    "\n".join([f'  - "{this_test}"' for this_test in passing_tests]),
                    file=pass_stream,
                )

            with StringIO() as temp_stream:
                with self.config["test_file"].open("r") as _input:
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
                self.config["test_file"].open("w").write(temp_stream.getvalue())

    def run(self) -> int:
        failed_or_not = super().run()

        self.move_passes_from_fail()

        return failed_or_not
