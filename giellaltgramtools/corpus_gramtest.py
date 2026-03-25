# -*- coding:utf-8 -*-

# Copyright © 2020-2026 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from pathlib import Path
from typing import Iterable

from click import Context

from giellaltgramtools.common import COLORS
from giellaltgramtools.corpus_config import CorpusConfig
from giellaltgramtools.corpus_gramchecker import CorpusGramChecker
from giellaltgramtools.gramtest import GramTest
from giellaltgramtools.normaloutput import NormalOutput
from giellaltgramtools.testdata import TestData


def fix_corpus_name(name: str) -> str:
    free_name_length = 2
    parts = name.split("-")
    if len(parts) == free_name_length:
        return f"{name}-orig"

    return "-".join([*parts[:free_name_length], "orig", *parts[free_name_length:]])


def do_replacements(path: Path) -> Path:
    parts = [
        fix_corpus_name(part) if part.startswith("corpus-") else part
        for part in path.parts
        if part not in ["converted", "goldstandard", "correct-no-gs"]
    ]
    new_path = Path(*parts)

    return new_path.with_name(new_path.name.replace(".xml", ""))


class CorpusGramTest(GramTest):
    def __init__(self, ctx: Context, ignore_typos: bool, targets: list[str]):
        super().__init__()
        self.targets = targets

        self.config: CorpusConfig = CorpusConfig(
            spec=Path(ctx.obj.get("spec", "")),
            variant=ctx.obj.get("variant", ""),
            output=NormalOutput(),
            hide_passes=ctx.obj.get("hide_passes", False),
            ignore_typos=ignore_typos,
        )

        if not ctx.obj.get("colour"):
            for key in list(COLORS.keys()):
                COLORS[key] = ""

    def get_error_data(self, filename: Path) -> list[str]:
        return [
            line
            for line in filename.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    def make_test_results(self) -> Iterable[TestData]:
        filenames = (
            do_replacements(path)
            for target in self.targets
            for path in Path(target).glob("**/*.xml")
        )

        grammarchecker = CorpusGramChecker(self.config)

        return (
            test_data
            for filename in filenames
            for test_data in grammarchecker.make_test_results(
                self.get_error_data(filename), filename=filename.as_posix()
            )
        )
