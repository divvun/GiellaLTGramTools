# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

from pathlib import Path

from giellaltgramtools.gramchecker import GramChecker


class CorpusGramChecker(GramChecker):
    """Check for grammarerrors in errormarkup files from a Giella corpus."""

    def __init__(self, archive, ignore_typos):
        super().__init__(ignore_typos)
        self.checker = self.app(archive)

    def app(self, archive: str):

        archive_file = Path(archive)
        if archive_file.is_file():
            return f"divvun-checker -a {archive_file}"
        else:
            raise SystemExit(f"The file {archive_file} does not exist")
