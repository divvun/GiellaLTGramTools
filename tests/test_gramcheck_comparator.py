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
                [["sjievnnjis", 9, 19, "errorort", "conc,vnn-vnnj", ["sjievnnijis"]]],
            ),
            (
                "<p><errormorphsyn>Nieiddat leat nuorra"
                '<correct errorinfo="a,spred,nompl,nomsg,agr">Nieiddat leat nuorat</correct>'  # noqa: E501
                "</errormorphsyn></p>",
                ["Nieiddat leat nuorra"],
                [
                    [
                        "Nieiddat leat nuorra",
                        0,
                        20,
                        "errormorphsyn",
                        "a,spred,nompl,nomsg,agr",
                        ["Nieiddat leat nuorat"],
                    ]
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
                    ["Nordkjosbotn ii", 6, 21, "errorort", "", ["Nordkjosbotnii"]],
                    ["nordkjosbotn", 34, 46, "errorort", "", ["Nordkjosbotn"]],
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
                [["šaddai", 0, 6, "errorort", "verb,conc", ["šattai"]]],
            ),
            (
                "<p>a "
                "<errorformat>"
                "b  c"
                '<correct errorinfo="notspace">b c</correct>'
                "</errorformat>"
                " d.</p>",
                ["a ", "b  c", " d."],
                [["b  c", 2, 6, "errorformat", "notspace", ["b c"]]],
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
                    [
                        "juhkkojuvvo",
                        9,
                        20,
                        "errormorphsyn",
                        "",
                        ["juhkkojuvvojedje", "juhkkojuvvojit"],
                    ],
                    [
                        "vuvdojuvvo",
                        26,
                        36,
                        "errormorphsyn",
                        "",
                        ["vuvdojuvvojedje", "vuvdojuvvojit"],
                    ],
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
                "<p>"
                "<errormorphsyn>"
                "<errorort>"
                "šaddai"
                '<correct errorinfo="verb,conc">šattai</correct>'
                "</errorort> ollu áššit"
                '<correct errorinfo="verb,fin,pl3prs,sg3prs,tense">šadde ollu áššit</correct>'  # noqa: E501
                "</errormorphsyn></p>",
                "<p>"
                "<errormorphsyn>"
                "šattai ollu áššit"
                '<correct errorinfo="verb,fin,pl3prs,sg3prs,tense">šadde ollu áššit</correct>'  # noqa: E501
                "</errormorphsyn></p>",
            )
        ]
    )
    def test_correct_lowest_level(self, para, wanted):
        corrected = self.gram_checker.correct_lowest_level(etree.fromstring(para))
        assert etree.tostring(corrected, encoding="unicode") == wanted

    @parameterized.expand(
        [
            (
                [
                    "“Dálveleaikkat“",
                    7,
                    22,
                    "punct-aistton-both",
                    "Boasttuaisttonmearkkat",
                    ["”Dálveleaikkat”"],
                    "Aisttonmearkkat",
                ],
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
                0,
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
    def test_fix_aistton_both(self, error, errors, position, wanted_errors):
        self.gram_checker.fix_aistton_both(error, errors, position)
        assert errors == wanted_errors

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
        assert self.gram_checker.fix_hidden_by_aistton_both(errors) == wanted_errors


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
