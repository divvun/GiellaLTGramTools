import pytest
from corpustools.error_annotated_sentence import (
    CorrectionSegment,
    ErrorAnnotatedSentence,
    ErrorMarkup,
    ErrorMarkupSegment,
)
from corpustools.error_types import ErrorType

from giellaltgramtools.errordata import ErrorData
from giellaltgramtools.grammar_error_annotated_sentence import (
    GrammarErrorAnnotatedSentence,
    error_annotated_sentence_to_grammar_error_annotated_sentence,
)


@pytest.mark.parametrize(
    ("name", "error_annotated_sentence", "expected_grammar_error_annotated_sentence"),
    [
        (
            "no errors",
            ErrorAnnotatedSentence(head="wrong", errors=[]),
            GrammarErrorAnnotatedSentence(sentence="wrong", errors=[]),
        ),
        (
            "single error",
            ErrorAnnotatedSentence(
                head="",
                errors=[
                    ErrorMarkupSegment(
                        error_markup=ErrorMarkup(
                            error=ErrorAnnotatedSentence(
                                head="molekylærbiologimi", errors=[]
                            ),
                            errortype=ErrorType.ERRORLANG,
                            correction=CorrectionSegment(
                                error_info="kal,bio",
                                suggestions=[""],
                            ),
                        ),
                        tail="",
                    )
                ],
            ),
            GrammarErrorAnnotatedSentence(
                sentence="molekylærbiologimi",
                errors=[
                    ErrorData(
                        error_string="molekylærbiologimi",
                        start=0,
                        end=18,
                        error_type="errorlang",
                        explanation="kal,bio",
                        suggestions=[""],
                    )
                ],
            ),
        ),
        (
            "non-nested errormarkups",
            ErrorAnnotatedSentence(
                head="a ",
                errors=[
                    ErrorMarkupSegment(
                        error_markup=ErrorMarkup(
                            error=ErrorAnnotatedSentence(head="e1", errors=[]),
                            errortype=ErrorType.ERRORORTREAL,
                            correction=CorrectionSegment(
                                error_info=None,
                                suggestions=["c1"],
                            ),
                        ),
                        tail=" b ",
                    ),
                    ErrorMarkupSegment(
                        error_markup=ErrorMarkup(
                            error=ErrorAnnotatedSentence(head="e2", errors=[]),
                            errortype=ErrorType.ERRORORT,
                            correction=CorrectionSegment(
                                error_info=None,
                                suggestions=["c2"],
                            ),
                        ),
                        tail=".",
                    ),
                ],
            ),
            GrammarErrorAnnotatedSentence(
                sentence="a e1 b e2.",
                errors=[
                    ErrorData(
                        error_string="e1",
                        start=2,
                        end=4,
                        error_type="errorortreal",
                        explanation="",
                        suggestions=["c1"],
                    ),
                    ErrorData(
                        error_string="e2",
                        start=7,
                        end=9,
                        error_type="errorort",
                        explanation="",
                        suggestions=["c2"],
                    ),
                ],
            ),
        ),
        (
            "many errors with nested errormarkups",
            ErrorAnnotatedSentence(
                head="heaitit ",
                errors=[
                    ErrorMarkupSegment(
                        error_markup=ErrorMarkup(
                            error=ErrorAnnotatedSentence(
                                head="dáhkaluddame", errors=[]
                            ),
                            errortype=ErrorType.ERRORORT,
                            correction=CorrectionSegment(
                                error_info="verb,a",
                                suggestions=["dahkaluddame"],
                            ),
                        ),
                        tail=" ahte sis ",
                    ),
                    ErrorMarkupSegment(
                        error_markup=ErrorMarkup(
                            error=ErrorAnnotatedSentence(head="máhkaš", errors=[]),
                            errortype=ErrorType.ERRORORTREAL,
                            correction=CorrectionSegment(
                                error_info="adv,á",
                                suggestions=["mahkáš"],
                            ),
                        ),
                        tail=" livččii ",
                    ),
                    ErrorMarkupSegment(
                        error_markup=ErrorMarkup(
                            error=ErrorAnnotatedSentence(head="makkarge", errors=[]),
                            errortype=ErrorType.ERRORORT,
                            correction=CorrectionSegment(
                                error_info="adv,á",
                                suggestions=["makkárge"],
                            ),
                        ),
                        tail=" politihkka, muhto rahpasit baicca muitalivčče ",
                    ),
                    ErrorMarkupSegment(
                        error_markup=ErrorMarkup(
                            error=ErrorAnnotatedSentence(
                                head="",
                                errors=[
                                    ErrorMarkupSegment(
                                        error_markup=ErrorMarkup(
                                            error=ErrorAnnotatedSentence(
                                                head="makkar", errors=[]
                                            ),
                                            errortype=ErrorType.ERRORORT,
                                            correction=CorrectionSegment(
                                                error_info="interr,á",
                                                suggestions=["makkár"],
                                            ),
                                        ),
                                        tail=" soga",
                                    )
                                ],
                            ),
                            errortype=ErrorType.ERRORLEX,
                            correction=CorrectionSegment(
                                error_info=None, suggestions=["man soga"]
                            ),
                        ),
                        tail=" sii ",
                    ),
                    ErrorMarkupSegment(
                        error_markup=ErrorMarkup(
                            error=ErrorAnnotatedSentence(head="ovddasttit", errors=[]),
                            errortype=ErrorType.ERRORORT,
                            correction=CorrectionSegment(
                                error_info="verb,conc",
                                suggestions=["ovddastit"],
                            ),
                        ),
                        tail=".",
                    ),
                ],
            ),
            GrammarErrorAnnotatedSentence(
                sentence=(
                    "heaitit dáhkaluddame ahte sis máhkaš livččii makkarge "
                    "politihkka, muhto rahpasit baicca muitalivčče makkar soga sii "
                    "ovddasttit."
                ),
                errors=[
                    ErrorData(
                        error_string="dáhkaluddame",
                        start=8,
                        end=20,
                        error_type="errorort",
                        explanation="verb,a",
                        suggestions=["dahkaluddame"],
                    ),
                    ErrorData(
                        error_string="máhkaš",
                        start=30,
                        end=36,
                        error_type="errorortreal",
                        explanation="adv,á",
                        suggestions=["mahkáš"],
                    ),
                    ErrorData(
                        error_string="makkarge",
                        start=45,
                        end=53,
                        error_type="errorort",
                        explanation="adv,á",
                        suggestions=["makkárge"],
                    ),
                    ErrorData(
                        error_string="makkar soga",
                        start=100,
                        end=111,
                        error_type="errorlex",
                        explanation="",
                        suggestions=["man soga"],
                    ),
                    ErrorData(
                        error_string="ovddasttit",
                        start=116,
                        end=126,
                        error_type="errorort",
                        explanation="verb,conc",
                        suggestions=["ovddastit"],
                    ),
                ],
            ),
        ),
    ],
)
def test_convert_error_annotated_sentence_to_grammar_error_annotated_sentence(
    name: str,
    error_annotated_sentence: ErrorAnnotatedSentence,
    expected_grammar_error_annotated_sentence: GrammarErrorAnnotatedSentence,
) -> None:
    grammar_error_annotated_sentence = (
        error_annotated_sentence_to_grammar_error_annotated_sentence(
            error_annotated_sentence
        )
    )
    assert (
        grammar_error_annotated_sentence == expected_grammar_error_annotated_sentence
    ), f'Test case "{name}" failed.'
