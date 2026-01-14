import pytest

from giellaltgramtools.divvun_runtime_fixes import divvun_runtime_to_aistton
from giellaltgramtools.errordata import ErrorData


@pytest.mark.parametrize(
    ("name", "input_error", "expected_converted_error"),
    [
        (
            "quotations-marks-to-aistton-both",
            ErrorData(
                error_string="«Skábmačuovggas»",
                start=36,
                end=52,
                error_type="quotation-marks",
                explanation="Leat boasttuaisttonmearkkat.",
                suggestions=("”Skábmačuovggas”Skábmačuovggas”",),
            ),
            ErrorData(
                error_string="«Skábmačuovggas»",
                start=36,
                end=52,
                error_type="punct-aistton-both",
                explanation="Leat boasttuaisttonmearkkat.",
                suggestions=("”Skábmačuovggas”Skábmačuovggas”",),
            ),
        ),
        (
            "quotations-marks-to-aistton-right",
            ErrorData(
                error_string="«Skábmačuovggas»",
                start=36,
                end=52,
                error_type="quotation-marks",
                explanation="Leat boasttuaisttonmearkkat.",
                suggestions=("Skábmačuovggas”Skábmačuovggas”",),
            ),
            ErrorData(
                error_string="«Skábmačuovggas»",
                start=36,
                end=52,
                error_type="punct-aistton-right",
                explanation="Leat boasttuaisttonmearkkat.",
                suggestions=("Skábmačuovggas”Skábmačuovggas”",),
            ),
        ),
        (
            "quotations-marks-to-aistton-left",
            ErrorData(
                error_string="«Skábmačuovggas»",
                start=36,
                end=52,
                error_type="quotation-marks",
                explanation="Leat boasttuaisttonmearkkat.",
                suggestions=("”Skábmačuovggas”Skábmačuovggas",),
            ),
            ErrorData(
                error_string="«Skábmačuovggas»",
                start=36,
                end=52,
                error_type="punct-aistton-left",
                explanation="Leat boasttuaisttonmearkkat.",
                suggestions=("”Skábmačuovggas”Skábmačuovggas",),
            ),
        ),
    ],
)
def test_quotations_marks_to_aistton_both(
    name: str, input_error: ErrorData, expected_converted_error: ErrorData
):
    fixed_error = divvun_runtime_to_aistton(input_error)

    assert fixed_error == expected_converted_error, f"Failed test case: {name}"


def test_quotations_marks_to_aistton_invalid():
    input_error = ErrorData(
        error_string="«Skábmačuovggas»",
        start=36,
        end=52,
        error_type="quotation-marks",
        explanation="Leat boasttuaisttonmearkkat.",
        suggestions=("SkábmačuovggasSkábmačuovggas",),
    )

    # Expect a specific ValueError message from divvun_runtime_to_aistton
    # Message format: "Cannot convert error with suggestions ... to aistton error."
    with pytest.raises(
        ValueError,
        match=r"^Cannot convert error with suggestions .* to aistton error\.$",
    ):
        divvun_runtime_to_aistton(input_error)
