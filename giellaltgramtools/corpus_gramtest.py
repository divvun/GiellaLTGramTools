# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

from curses import COLORS

from corpustools import ccat  # type: ignore
from lxml import etree

from giellaltgramtools.corpus_gramchecker import CorpusGramChecker
from giellaltgramtools.gramtest import GramTest


class CorpusGramTest(GramTest):
    def __init__(self, args):
        super().__init__()
        self.ignore_typos = args.ignore_typos
        self.archive = args.archive
        self.targets = args.targets
        self.config = {"out": GramTest.NormalOutput(args)}
        if not args.colour:
            for key in list(COLORS.keys()):
                COLORS[key] = ""

    def flatten_para(self, para):
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

    def keep_url(self, root):
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

    def get_error_data(self, filename, grammarchecker):
        root = etree.parse(filename)
        self.keep_url(root)
        for para in root.iter("p"):
            # the xml:lang attribute indicates that the sentence is not the expected
            # language. These paragraphs are not included in the test.
            if not para.get("{http://www.w3.org/XML/1998/namespace}lang"):
                self.flatten_para(para)
                yield grammarchecker.paragraph_to_testdata(para)

    @property
    def paragraphs(self):
        grammarchecker = CorpusGramChecker(self.archive, self.ignore_typos)

        for filename in ccat.find_files(self.targets, ".xml"):
            root = etree.parse(filename)
            self.keep_url(root)
            error_datas = list(self.get_error_data(filename, grammarchecker))
            grammar_datas = grammarchecker.check_paragraphs(
                "\n".join(error_data[0] for error_data in error_datas)
            )
            for item in zip(error_datas, grammar_datas, strict=True):
                yield grammarchecker.clean_data(
                    sentence=item[0],
                    expected_errors=item[1],
                    gramcheck_errors=item[2],
                    filename=filename,
                )
