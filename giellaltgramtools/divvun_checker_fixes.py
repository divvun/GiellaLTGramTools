from typing import Iterator

from giellaltgramtools.errordata import ErrorData


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
    d_errors: list[ErrorData],
) -> list[ErrorData]:
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
