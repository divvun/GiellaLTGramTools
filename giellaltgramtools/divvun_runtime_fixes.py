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
    first_suggestion = error_data.suggestions[0] if error_data.suggestions else ""
    if first_suggestion.startswith("”") and first_suggestion.endswith("”"):
        new_error_type = "punct-aistton-both"
    elif first_suggestion.startswith("”"):
        new_error_type = "punct-aistton-left"
    elif first_suggestion.endswith("”"):
        new_error_type = "punct-aistton-right"
    else:
        raise ValueError(
            f"Cannot convert error with suggestions {error_data.suggestions} "
            "to aistton error."
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
