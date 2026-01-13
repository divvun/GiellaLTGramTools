"""Test grammarcheck tester functionality"""

import os
from pathlib import Path

import pytest

from giellaltgramtools.corpus_gramchecker import CorpusGramChecker
from giellaltgramtools.errordata import ErrorData
from giellaltgramtools.gramtest import GramTest
from giellaltgramtools.normaloutput import NormalOutput


@pytest.fixture
def gram_checker():
    gtlangs = os.getenv("GTLANGS")
    if gtlangs is not None:
        return CorpusGramChecker(
            config={
                "out": NormalOutput(),
                "ignore_typos": False,
                "spec": Path(gtlangs) / "lang-sme/tools/grammarcheckers/pipespec.xml",
                "variants": ["smegram-dev"],
            }
        )
    else:
        raise ValueError("GTLANGS environment variable not set")




@pytest.fixture
def gram_test():
    return GramTest()


@pytest.mark.parametrize(
    ("c_error", "d_error", "expected_boolean"),
    [
        (
            ErrorData(
                error_string="c",
                start=3,
                end=6,
                error_type="",
                explanation="",
                suggestions=("b",),
            ),
            ErrorData(
                error_string="c",
                start=3,
                end=6,
                error_type="",
                explanation="",
                suggestions=("b",),
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
                suggestions=("b",),
            ),
            ErrorData(
                error_string="c",
                start=3,
                end=6,
                error_type="",
                explanation="",
                suggestions=(),
            ),
            True,
        ),
    ],
)
def test_has_no_suggesions(gram_test, c_error, d_error, expected_boolean):
    assert gram_test.has_no_suggestions(c_error, d_error) == expected_boolean


@pytest.mark.parametrize(
    ("c_error", "d_error", "expected_boolean"),
    [
        (
            ErrorData(
                error_string="c",
                start=3,
                end=6,
                error_type="",
                explanation="",
                suggestions=(),
            ),
            ErrorData(
                error_string="",
                start=3,
                end=6,
                error_type="double-space-before",
                explanation="",
                suggestions=(),
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
                suggestions=("b",),
            ),
            ErrorData(
                error_string="c",
                start=3,
                end=6,
                error_type="double-space-before",
                explanation="",
                suggestions=("a",),
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
                suggestions=(),
            ),
            ErrorData(
                error_string="c",
                start=3,
                end=6,
                error_type="msyn",
                explanation="",
                suggestions=(),
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
                suggestions=("a",),
            ),
            ErrorData(
                error_string="c",
                start=3,
                end=6,
                error_type="msyn",
                explanation="",
                suggestions=("a", "b"),
            ),
            True,
        ),
    ],
)
def test_suggestion_with_hits(gram_test, c_error, d_error, expected_boolean):
    assert gram_test.has_suggestions_with_hit(c_error, d_error) == expected_boolean


@pytest.mark.parametrize(
    ("c_error", "d_error", "expected_boolean"),
    [
        (
            ErrorData(
                error_string="c",
                start=3,
                end=6,
                error_type="",
                explanation="",
                suggestions=(),
            ),
            ErrorData(
                error_string="",
                start=3,
                end=6,
                error_type="double-space-before",
                explanation="",
                suggestions=(),
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
                suggestions=(),
            ),
            ErrorData(
                error_string="",
                start=2,
                end=5,
                error_type="double-space-before",
                explanation="",
                suggestions=(),
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
                suggestions=(),
            ),
            ErrorData(
                error_string="d",
                start=3,
                end=6,
                error_type="msyn",
                explanation="",
                suggestions=(),
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
                suggestions=(),
            ),
            ErrorData(
                error_string="c",
                start=2,
                end=6,
                error_type="msyn",
                explanation="",
                suggestions=(),
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
                suggestions=(),
            ),
            ErrorData(
                error_string="c",
                start=3,
                end=5,
                error_type="msyn",
                explanation="",
                suggestions=(),
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
                suggestions=(),
            ),
            ErrorData(
                error_string="c",
                start=3,
                end=6,
                error_type="msyn",
                explanation="",
                suggestions=(),
            ),
            True,
        ),
    ],
)
def test_same_range_and_error(gram_test, c_error, d_error, expected_boolean):
    assert gram_test.has_same_range_and_error(c_error, d_error) == expected_boolean
