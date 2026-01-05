import pytest
from corpustools.error_annotated_sentence import (
    CorrectionSegment,
    ErrorAnnotatedSentence,
    ErrorMarkup,
    ErrorMarkupSegment,
)
from corpustools.error_types import ErrorType

from giellaltgramtools.errordata import ErrorData, error_markup_to_error_data


@pytest.mark.parametrize(
    ("name", "error_markup", "offset", "error_data"),
    [
        (
            "non-nested error markup with explanation",
            ErrorMarkup(
                error=ErrorAnnotatedSentence(head="molekylærbiologimi", errors=[]),
                errortype=ErrorType.ERRORLANG,
                correction=CorrectionSegment(
                    error_info="kal,bio",
                    suggestions=[""],
                ),
            ),
            0,
            ErrorData(
                error_string="molekylærbiologimi",
                start=0,
                end=18,
                error_type="errorlang",
                explanation="kal,bio",
                suggestions=[""],
            ),
        ),
        (
            "non-nested error markup without explanation",
            ErrorMarkup(
                error=ErrorAnnotatedSentence(head="1]", errors=[]),
                errortype=ErrorType.ERROR,
                correction=CorrectionSegment(
                    error_info=None,
                    suggestions=["Ij"],
                ),
            ),
            5,
            ErrorData(
                error_string="1]",
                start=5,
                end=7,
                error_type="error",
                explanation="",
                suggestions=["Ij"],
            ),
        ),
        (
            "nested error markup",
            ErrorMarkup(
                error=ErrorAnnotatedSentence(
                    head="",
                    errors=[
                        ErrorMarkupSegment(
                            error_markup=ErrorMarkup(
                                error=ErrorAnnotatedSentence(head="A  B", errors=[]),
                                errortype=ErrorType.ERRORFORMAT,
                                correction=CorrectionSegment(
                                    error_info="notspace",
                                    suggestions=["A B"],
                                ),
                            ),
                            tail="  C",
                        )
                    ],
                ),
                errortype=ErrorType.ERRORFORMAT,
                correction=CorrectionSegment(
                    error_info="notspace",
                    suggestions=["A B C"],
                ),
            ),
            2,
            ErrorData(
                error_string="A  B  C",
                start=2,
                end=9,
                error_type="errorformat",
                explanation="notspace",
                suggestions=["A B C"],
            ),
        ),
    ],
)
def test_error_markup_to_error_data(
    name: str,
    error_markup: ErrorMarkup,
    offset: int,
    error_data: list[ErrorData],
) -> None:
    result = error_markup_to_error_data(error_markup, offset)

    assert result == error_data, f"Failed test case: {name}"
