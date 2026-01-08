from giellaltgramtools.errordata import (
    ErrorData,
    fix_aistton_both,
    fix_aistton_left,
    fix_aistton_right,
)


def test_fix_aistton_both():
    input_error = ErrorData(
        error_string="«Skábmačuovggas»",
        start=36,
        end=52,
        error_type="punct-aistton-both",
        explanation="Leat boasttuaisttonmearkkat.",
        suggestions=["”Skábmačuovggas”Skábmačuovggas”"],
    )

    expected_fixed_errors = [
        ErrorData(
            error_string="«",
            start=36,
            end=37,
            error_type="punct-aistton-both",
            explanation="Leat boasttuaisttonmearkkat.",
            suggestions=["”"],
        ),
        ErrorData(
            error_string="»",
            start=51,
            end=52,
            error_type="punct-aistton-both",
            explanation="Leat boasttuaisttonmearkkat.",
            suggestions=["”"],
        ),
    ]

    fixed_errors = list(fix_aistton_both(input_error))

    assert fixed_errors == expected_fixed_errors

def test_fix_aistton_right():
    input_error = ErrorData(
        error_string='sávzzat"',
        start=6,
        end=14,
        error_type="punct-aistton-right",
        explanation="Leat boasttuaisttonmearkkat.",
        suggestions=["sávzzat”"],
    )

    expected_fixed_error  = ErrorData(
            error_string='"',
            start=13,
            end=14,
            error_type="punct-aistton-right",
            explanation="Leat boasttuaisttonmearkkat.",
            suggestions=["”"],
        )

    fixed_error = fix_aistton_right(input_error)

    assert fixed_error == expected_fixed_error

def test_fix_aistton_left():
    input_error = ErrorData(
        error_string='«sávzzat',
        start=0,
        end=8,
        error_type="punct-aistton-left",
        explanation="Leat boasttuaisttonmearkkat.",
        suggestions=["“sávzzat"],
    )

    expected_fixed_error  = ErrorData(
            error_string="«",
            start=0,
            end=1,
            error_type="punct-aistton-left",
            explanation="Leat boasttuaisttonmearkkat.",
            suggestions=["“"],
        )

    fixed_error = fix_aistton_left(input_error)

    assert fixed_error == expected_fixed_error