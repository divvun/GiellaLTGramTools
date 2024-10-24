"""Test grammarcheck tester functionality"""

import os
import unittest
from pathlib import Path

from lxml import etree
from parameterized import parameterized

from giellaltgramtools.corpus_gramchecker import CorpusGramChecker
from giellaltgramtools.errordata import ErrorData
from giellaltgramtools.gramtest import GramTest
from giellaltgramtools.normaloutput import NormalOutput


class TestGramChecker(unittest.TestCase):
    """Test grammarcheck tester"""

    def setUp(self) -> None:
        gtlangs = os.getenv("GTLANGS")
        if gtlangs is not None:
            self.gram_checker = CorpusGramChecker(
                config={
                    "out": NormalOutput(args={}),
                    "ignore_typos": False,
                    "spec": Path(gtlangs)
                    / "lang-sme/tools/grammarcheckers/pipespec.xml",
                    "variants": ["smegram-dev"],
                }
            )
            return super().setUp()
        else:
            raise ValueError("GTLANGS environment variable not set")

    @parameterized.expand(
        [
            (
                '<p>Mun lean <errorort>sjievnnjis<correct errorinfo="conc,vnn-vnnj">sjievnnijis</correct></errorort></p>',  # noqa: E501
                ["Mun lean ", "sjievnnjis"],
                [
                    ErrorData(
                        error_string="sjievnnjis",
                        start=9,
                        end=19,
                        error_type="errorort",
                        explanation="conc,vnn-vnnj",
                        suggestions=["sjievnnijis"],
                        native_error_type="errorort",
                    )
                ],
            ),
            (
                "<p><errormorphsyn>Nieiddat leat nuorra"
                '<correct errorinfo="a,spred,nompl,nomsg,agr">Nieiddat leat nuorat</correct>'  # noqa: E501
                "</errormorphsyn></p>",
                ["Nieiddat leat nuorra"],
                [
                    ErrorData(
                        error_string="Nieiddat leat nuorra",
                        start=0,
                        end=20,
                        error_type="errormorphsyn",
                        explanation="a,spred,nompl,nomsg,agr",
                        suggestions=["Nieiddat leat nuorat"],
                        native_error_type="errormorphsyn",
                    )
                ],
            ),
            (
                "<p>gitta "
                "<errorort>Nordkjosbotn ii<correct>Nordkjosbotnii</correct></errorort> "
                "(mii lea ge "
                "<errorort>nordkjosbotn<correct>Nordkjosbotn</correct></errorort> "
                "sámegillii? Muhtin, veahket mu!) gos</p>",
                [
                    "gitta ",
                    "Nordkjosbotn ii",
                    " (mii lea ge ",
                    "nordkjosbotn",
                    " sámegillii? Muhtin, veahket mu!) gos",
                ],
                [
                    ErrorData(
                        error_string="Nordkjosbotn ii",
                        start=6,
                        end=21,
                        error_type="errorort",
                        explanation="",
                        suggestions=["Nordkjosbotnii"],
                        native_error_type="errorort",
                    ),
                    ErrorData(
                        error_string="nordkjosbotn",
                        start=34,
                        end=46,
                        error_type="errorort",
                        explanation="",
                        suggestions=["Nordkjosbotn"],
                        native_error_type="errorort",
                    ),
                ],
            ),
            (
                "<p>"
                "<errormorphsyn>"
                "<errorort>"
                "šaddai"
                '<correct errorinfo="verb,conc">šattai</correct>'
                "</errorort> ollu áššit"
                '<correct errorinfo="verb,fin,pl3prs,sg3prs,tense">šadde ollu áššit</correct>'  # noqa: E501
                "</errormorphsyn></p>",
                ["šaddai", " ollu áššit"],
                [
                    ErrorData(
                        error_string="šaddai",
                        start=0,
                        end=6,
                        error_type="errorort",
                        explanation="verb,conc",
                        suggestions=["šattai"],
                        native_error_type="errorort",
                    )
                ],
            ),
            (
                "<p>a "
                "<errorformat>"
                "b  c"
                '<correct errorinfo="notspace">b c</correct>'
                "</errorformat>"
                " d.</p>",
                ["a ", "b  c", " d."],
                [
                    ErrorData(
                        error_string="b  c",
                        start=2,
                        end=6,
                        error_type="errorformat",
                        explanation="notspace",
                        suggestions=["b c"],
                        native_error_type="errorformat",
                    )
                ],
            ),
            (
                "<p>Kondomat <errormorphsyn>juhkkojuvvo<correct>juhkkojuvvojedje</correct><correct>juhkkojuvvojit</correct></errormorphsyn> dehe <errormorphsyn>vuvdojuvvo<correct>vuvdojuvvojedje</correct><correct>vuvdojuvvojit</correct></errormorphsyn> nuoraidvuostáváldimis.</p>",  # noqa: E501
                [
                    "Kondomat ",
                    "juhkkojuvvo",
                    " dehe ",
                    "vuvdojuvvo",
                    " nuoraidvuostáváldimis.",
                ],
                [
                    ErrorData(
                        error_string="juhkkojuvvo",
                        start=9,
                        end=20,
                        error_type="errormorphsyn",
                        explanation="",
                        suggestions=["juhkkojuvvojedje", "juhkkojuvvojit"],
                        native_error_type="errormorphsyn",
                    ),
                    ErrorData(
                        error_string="vuvdojuvvo",
                        start=26,
                        end=36,
                        error_type="errormorphsyn",
                        explanation="",
                        suggestions=["vuvdojuvvojedje", "vuvdojuvvojit"],
                        native_error_type="errormorphsyn",
                    ),
                ],
            ),
        ]
    )
    def test_extract_error_info(self, paragraph, want_parts, want_errors):
        parts = []
        errors = []
        self.gram_checker.extract_error_info(parts, errors, etree.fromstring(paragraph))

        assert parts == want_parts
        assert errors == want_errors

    @parameterized.expand(
        [
            (
                [
                    [
                        "“Dálveleaikkat“",
                        7,
                        22,
                        "punct-aistton-both",
                        "Boasttuaisttonmearkkat",
                        ["”Dálveleaikkat”"],
                        "Aisttonmearkkat",
                    ]
                ],
                [
                    [
                        "“",
                        7,
                        8,
                        "punct-aistton-both",
                        "Boasttuaisttonmearkkat",
                        ["”"],
                        "Aisttonmearkkat",
                    ],
                    [
                        "“",
                        21,
                        22,
                        "punct-aistton-both",
                        "Boasttuaisttonmearkkat",
                        ["”"],
                        "Aisttonmearkkat",
                    ],
                ],
            )
        ]
    )
    def test_fix_aistton_both(self, errors, wanted_errors):
        my_errors = self.gram_checker.fix_aistton(errors)
        assert list(my_errors) == wanted_errors

    @parameterized.expand(
        [
            (
                [
                    [
                        '"Goaskin viellja"',
                        15,
                        32,
                        "msyn-compound",
                        '"Goaskin viellja" orru leamen goallossátni',
                        ['"Goaskinviellja"'],
                        "Goallosteapmi",
                    ],
                    [
                        '"Goaskin viellja"',
                        15,
                        32,
                        "punct-aistton-both",
                        "Boasttuaisttonmearkkat",
                        ["”Goaskin viellja”"],
                        "Aisttonmearkkat",
                    ],
                ],
                [
                    [
                        "Goaskin viellja",
                        16,
                        31,
                        "msyn-compound",
                        '"Goaskin viellja" orru leamen goallossátni',
                        ["Goaskinviellja"],
                        "Goallosteapmi",
                    ],
                    [
                        '"Goaskin viellja"',
                        15,
                        32,
                        "punct-aistton-both",
                        "Boasttuaisttonmearkkat",
                        ["”Goaskin viellja”"],
                        "Aisttonmearkkat",
                    ],
                ],
            ),
            (
                [
                    [
                        "dálve olympiijagilvvuid",
                        22,
                        45,
                        "msyn-compound",
                        '"dálve olympiijagilvvuid" orru leamen goallossátni',
                        ["dálveolympiagilvvuid"],
                        "Goallosteapmi",
                    ],
                    [
                        "CDa",
                        53,
                        56,
                        "typo",
                        "Ii leat sátnelisttus",
                        ["CD"],
                        "Čállinmeattáhus",
                    ],
                    [
                        "“Dálveleaikat“",
                        78,
                        92,
                        "real-PlNomPxSg2-PlNom",
                        "Sátni šaddá eará go oaivvilduvvo",
                        ["“Dálveleaikkat“"],
                        "Čállinmeattáhus dán oktavuođas",
                    ],
                    [
                        "“Dálveleaikat“",
                        78,
                        92,
                        "punct-aistton-both",
                        "Boasttuaisttonmearkkat",
                        ["”Dálveleaikat”"],
                        "Aisttonmearkkat",
                    ],
                ],
                [
                    [
                        "dálve olympiijagilvvuid",
                        22,
                        45,
                        "msyn-compound",
                        '"dálve olympiijagilvvuid" orru leamen goallossátni',
                        ["dálveolympiagilvvuid"],
                        "Goallosteapmi",
                    ],
                    [
                        "CDa",
                        53,
                        56,
                        "typo",
                        "Ii leat sátnelisttus",
                        ["CD"],
                        "Čállinmeattáhus",
                    ],
                    [
                        "Dálveleaikat",
                        79,
                        91,
                        "real-PlNomPxSg2-PlNom",
                        "Sátni šaddá eará go oaivvilduvvo",
                        ["Dálveleaikkat"],
                        "Čállinmeattáhus dán oktavuođas",
                    ],
                    [
                        "“Dálveleaikat“",
                        78,
                        92,
                        "punct-aistton-both",
                        "Boasttuaisttonmearkkat",
                        ["”Dálveleaikat”"],
                        "Aisttonmearkkat",
                    ],
                ],
            ),
        ]
    )
    def test_fix_hidden_by_aistton_both(self, errors, wanted_errors):
        assert self.gram_checker.fix_hidden_by_aistton(errors) == wanted_errors


class TestGramTester(unittest.TestCase):
    """Test grammarcheck tester"""

    def setUp(self) -> None:
        self.gram_test = GramTest()
        return super().setUp()

    @parameterized.expand(
        [
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="",
                    explanation="",
                    suggestions=[],
                ),
                ErrorData(
                    error_string="",
                    start=3,
                    end=6,
                    error_type="double-space-before",
                    explanation="",
                    suggestions=[],
                ),
                True,
            ),
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="",
                    explanation="",
                    suggestions=[],
                ),
                ErrorData(
                    error_string="",
                    start=2,
                    end=5,
                    error_type="double-space-before",
                    explanation="",
                    suggestions=[],
                ),
                False,
            ),
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="errorsyn",
                    explanation="",
                    suggestions=[],
                ),
                ErrorData(
                    error_string="d",
                    start=3,
                    end=6,
                    error_type="msyn",
                    explanation="",
                    suggestions=[],
                ),
                False,
            ),
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="errorsyn",
                    explanation="",
                    suggestions=[],
                ),
                ErrorData(
                    error_string="c",
                    start=2,
                    end=6,
                    error_type="msyn",
                    explanation="",
                    suggestions=[],
                ),
                False,
            ),
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="errorsyn",
                    explanation="",
                    suggestions=[],
                ),
                ErrorData(
                    error_string="c",
                    start=3,
                    end=5,
                    error_type="msyn",
                    explanation="",
                    suggestions=[],
                ),
                False,
            ),
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="errorsyn",
                    explanation="",
                    suggestions=[],
                ),
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="msyn",
                    explanation="",
                    suggestions=[],
                ),
                True,
            ),
        ]
    )
    def test_same_range_and_error(self, c_error, d_error, expected_boolean):
        assert (
            self.gram_test.has_same_range_and_error(c_error, d_error)
            == expected_boolean
        )

    @parameterized.expand(
        [
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="",
                    explanation="",
                    suggestions=[],
                ),
                ErrorData(
                    error_string="",
                    start=3,
                    end=6,
                    error_type="double-space-before",
                    explanation="",
                    suggestions=[],
                ),
                False,
            ),
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="",
                    explanation="",
                    suggestions=["b"],
                ),
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="double-space-before",
                    explanation="",
                    suggestions=["a"],
                ),
                False,
            ),
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="errorsyn",
                    explanation="",
                    suggestions=[],
                ),
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="msyn",
                    explanation="",
                    suggestions=[],
                ),
                False,
            ),
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="errorsyn",
                    explanation="",
                    suggestions=["a"],
                ),
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="msyn",
                    explanation="",
                    suggestions=["a", "b"],
                ),
                True,
            ),
        ]
    )
    def test_suggestion_with_hits(self, c_error, d_error, expected_boolean):
        assert (
            self.gram_test.has_suggestions_with_hit(c_error, d_error)
            == expected_boolean
        )

    @parameterized.expand(
        [
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="",
                    explanation="",
                    suggestions=["b"],
                ),
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="",
                    explanation="",
                    suggestions=["b"],
                ),
                False,
            ),
            (
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="",
                    explanation="",
                    suggestions=["b"],
                ),
                ErrorData(
                    error_string="c",
                    start=3,
                    end=6,
                    error_type="",
                    explanation="",
                    suggestions=[],
                ),
                True,
            ),
        ]
    )
    def test_has_no_suggesions(self, c_error, d_error, expected_boolean):
        assert self.gram_test.has_no_suggestions(c_error, d_error) == expected_boolean
