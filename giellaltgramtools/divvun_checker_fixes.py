from typing import Iterable, Iterator

from giellaltgramtools.errordata import ErrorData
from giellaltgramtools.errordatas import ErrorDatas


def sort_by_range(errors: Iterable[ErrorData]) -> ErrorDatas:
    """Sort error data by their range in the text.

    Args:
        errors (Iterable[ErrorData]): List of error data to sort.
    Returns:
        ErrorDatas sorted by their start and end positions.
    """
    return tuple(sorted(errors, key=lambda error: (error.start, error.end)))

def fix_aistton_both(aistton_both: ErrorData) -> Iterator[ErrorData]:
    """Split divvun-checker punct-aistton-both error into two separate errors.

    Args:
        aistton_both (ErrorData): The original error data representing both errors.

    Yields:
        Two separate ErrorData that mimics the manual error markup.
    """
    yield ErrorData(
        error_string=aistton_both.error_string[0],
        start=aistton_both.start,
        end=aistton_both.start + 1,
        error_type=aistton_both.error_type,
        explanation=aistton_both.explanation,
        suggestions=(aistton_both.suggestions[0][0],),
    )
    yield ErrorData(
        error_string=aistton_both.error_string[-1],
        start=aistton_both.end - 1,
        end=aistton_both.end,
        error_type=aistton_both.error_type,
        explanation=aistton_both.explanation,
        suggestions=(aistton_both.suggestions[-1][-1],),
    )


def fix_aistton_right(aistton_right: ErrorData) -> ErrorData:
    """Fix divvun-checker punct-aistton-right error to match manual error markup.

    Args:
        The original error data representing the right aistton error.
    Returns:
        Fixed ErrorData that mimics the manual error markup.
    """
    return ErrorData(
        error_string=aistton_right.error_string[-1],
        start=aistton_right.end - 1,
        end=aistton_right.end,
        error_type=aistton_right.error_type,
        explanation=aistton_right.explanation,
        suggestions=(aistton_right.suggestions[0][-1],),
    )


def fix_aistton_left(aistton_left: ErrorData) -> ErrorData:
    """Fix divvun-checker punct-aistton-left error to match manual error markup.

    Args:
        The original error data representing the left aistton error.
    Returns:
        Fixed ErrorData that mimics the manual error markup.
    """
    return ErrorData(
        error_string=aistton_left.error_string[0],
        start=aistton_left.start,
        end=aistton_left.start + 1,
        error_type=aistton_left.error_type,
        explanation=aistton_left.explanation,
        suggestions=(aistton_left.suggestions[0][0],),
    )


def remove_aistton(errors: list[ErrorData]) -> list[ErrorData]:
    """Remove divvun-checker punct-aistton errors from the list of error data.

    They cover the same issues as punct-aistton-left and punct-aistton-right.

    Args:
        errors (list[ErrorData]): The original list of error data
    Returns:
        List of ErrorData with punct-aistton errors removed.
    """
    return [error for error in errors if not error.error_type == "punct-aistton"]


def fix_hidden_by_aistton(
    d_errors: Iterable[ErrorData],
) -> Iterable[ErrorData]:
    """Fix errors hidden by aistton-both errors.

    A GramDivvun error of type aistton-both can contain some other error.
    The other error is reported as having the same range as the aistton-both error.

    This function fixes the range to match the marked up error.

    Args:
        d_errors: List of GramDivvun errors.

    Returns:
        list: List of GramDivvun errors with the hidden errors revealed.
    """

    def is_hidden_error(
        error: ErrorData,
    ) -> bool:
        return (error.start, error.end) in aistton_ranges and error.error_type not in [
            "punct-aistton-both",
            "punct-aistton-left",
            "punct-aistton-right",
        ]

    def fix_hidden_error(
        error: ErrorData,
    ) -> ErrorData:
        if error.error_type == "punct-aistton-left":
            return ErrorData(
                error_string=error.error_string[1:],
                start=error.start + 1,
                end=error.end,
                error_type=error.error_type,
                explanation=error.explanation,
                suggestions=tuple(suggestion[1:] for suggestion in error.suggestions),
            )
        if error.error_type == "punct-aistton-right":
            return ErrorData(
                error_string=error.error_string[:-1],
                start=error.start,
                end=error.end - 1,
                error_type=error.error_type,
                explanation=error.explanation,
                suggestions=tuple(suggestion[:-1] for suggestion in error.suggestions),
            )

        return ErrorData(
            error_string=error.error_string[1:-1],
            start=error.start + 1,
            end=error.end - 1,
            error_type=error.error_type,
            explanation=error.explanation,
            suggestions=tuple(suggestion[1:-1] for suggestion in error.suggestions),
        )

    aistton_ranges = [
        (error.start, error.end)
        for error in d_errors
        if error.error_type
        in ["punct-aistton-both", "punct-aistton-left", "punct-aistton-right"]
    ]
    return [
        fix_hidden_error(error) if is_hidden_error(error) else error
        for error in d_errors
    ]

def fix_aistton(
    d_errors: Iterable[ErrorData],
) -> Iterator[ErrorData]:
    """Rearrange GramDivvun aistton errors to match the Giella markup format.

    GramDivvun marks up errors with wrong quotemarks by including the word next to
    the quote marks.

    The manual error markup, on the other hand, only marks up the quote marks.

    Args:
        d_errors: Iterable of GramDivvun errors.
    Returns:
        Iterator of GramDivvun errors with aistton errors fixed.
    """
    for d_error in fix_hidden_by_aistton(d_errors):
        # Skip punct-aistton errors
        # punct-aistton are emitted together with
        # punct-aistton-left and punct-aistton-right
        if d_error.error_type != "punct-aistton":
            if d_error.error_type == "punct-aistton-both":
                yield from fix_aistton_both(d_error)
            elif d_error.error_type == "punct-aistton-left":
                yield fix_aistton_left(d_error)
            elif d_error.error_type == "punct-aistton-right":
                yield fix_aistton_right(d_error)
            else:
                yield d_error


