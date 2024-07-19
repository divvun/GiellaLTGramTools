# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>


from pathlib import Path
from typing import Iterable

from corpustools import ccat  # type: ignore
from lxml.etree import _Element, _ElementTree, parse

from giellaltgramtools.common import COLORS
from giellaltgramtools.corpus_gramchecker import CorpusGramChecker
from giellaltgramtools.errordata import ErrorData
from giellaltgramtools.gramtest import GramTest
from giellaltgramtools.normaloutput import NormalOutput
from giellaltgramtools.testdata import TestData


class CorpusGramTest(GramTest):
    def __init__(self, args: dict[str, str], ignore_typos: bool, targets: list[str]):
        super().__init__()
        self.targets = targets

        self.config = {
            "out": NormalOutput(args),
            "ignore_typos": ignore_typos,
            "spec": Path(args.get("spec", "")),
            "variants": [args.get("variant")],
        }
        if not args.get("colour"):
            for key in list(COLORS.keys()):
                COLORS[key] = ""

    def flatten_para(self, para: _Element) -> None:
        """Convert non-error xml elements into plain text."""
        if not (para.tag.startswith("error") or para.tag == "correct"):
            text = para.text if para.text else ""

            if para.tail:
                text += para.tail

            parent = para.getparent()
            if parent is not None:
                parent.remove(para)
                if parent.text:
                    parent.text = parent.text + text
                else:
                    parent.text = text

        for child in para:
            self.flatten_para(child)

    def keep_url(self, root: _ElementTree) -> None:  # noqa: PLR0912, C901
        """Keep url as plain text."""
        for url in root.xpath('.//errorlang[@correct="url"]'):
            parent = url.getparent()
            previous = url.getprevious()
            if previous is not None:
                if url.text is not None:
                    if previous.tail is not None:
                        previous.tail += url.text
                    else:
                        previous.tail = url.text
                if url.tail is not None:
                    if previous.tail is not None:
                        previous.tail += url.tail
                    else:
                        previous.tail = url.tail
            else:
                if url.text is not None:
                    if parent.text is not None:
                        parent.text += url.text
                    else:
                        parent.text = url.text
                if url.tail is not None:
                    if parent.text is not None:
                        parent.text += url.tail
                    else:
                        parent.text = url.tail

            parent.remove(url)

    def get_error_data(
        self, filename: str, grammarchecker: CorpusGramChecker
    ) -> Iterable[tuple[str, list[ErrorData]]]:
        root: _ElementTree = parse(filename)
        self.keep_url(root)
        for para in root.iter("p"):
            # the xml:lang attribute indicates that the sentence is not the expected
            # language. These paragraphs are not included in the test.
            if not para.get("{http://www.w3.org/XML/1998/namespace}lang"):
                self.flatten_para(para)
                yield grammarchecker.paragraph_to_testdata(para)

    def make_test_results(self) -> Iterable[TestData]:
        grammarchecker = CorpusGramChecker(self.config)

        for filename in ccat.find_files(self.targets, ".xml"):
            root = parse(filename)
            self.keep_url(root)
            error_datas = list(self.get_error_data(filename, grammarchecker))
            grammar_datas = grammarchecker.check_paragraphs(
                "\n".join(error_data[0].rstrip() for error_data in error_datas)
            )
            for item in zip(error_datas, grammar_datas, strict=True):
                yield grammarchecker.clean_data(
                    sentence=item[0][0],
                    expected_errors=item[0][1],
                    gramcheck_errors=item[1],
                    filename=filename,
                )
