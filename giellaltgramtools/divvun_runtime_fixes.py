from giellaltgramtools.errordata import ErrorData


def divvun_runtime_to_aistton(
    error_data: ErrorData,
) -> ErrorData:
    """Convert divvun-runtime quotation-marks errors to Giella aistton errors.

    Args:
        error_data: ErrorData object representing a divvun-runtime quotation-marks
            error.
    Returns:
        ErrorData object representing a Giella aistton error.
    """
    if not error_data.suggestions:
        raise ValueError(
            f"Cannot convert error with no suggestions to aistton error.\n"
            f"{error_data!r}"
        )

    first_suggestion = error_data.suggestions[0]
    if first_suggestion[0] in "”’" and first_suggestion[-1] in "”’":
        new_error_type = "punct-aistton-both"
    elif first_suggestion[0] in "”’" :
        new_error_type = "punct-aistton-left"
    elif first_suggestion[-1] in "”’":
        new_error_type = "punct-aistton-right"
    else:
        raise ValueError(
            f"Cannot convert error with suggestions {error_data.suggestions} "
            f"to aistton error.\n{error_data!r}"
        )

    # Create new ErrorData object with updated error_type and explanation
    new_error_data = ErrorData(
        error_string=error_data.error_string,
        start=error_data.start,
        end=error_data.end,
        error_type=new_error_type,
        explanation=error_data.explanation,
        suggestions=error_data.suggestions,
    )
    return new_error_data
