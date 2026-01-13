import pytest

from giellaltgramtools.divvun_checker_fixes import (
    fix_aistton_both,
    fix_aistton_left,
    fix_aistton_right,
    fix_hidden_by_aistton,
    remove_aistton,
)
from giellaltgramtools.errordata import (
    ErrorData,
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

    expected_fixed_error = ErrorData(
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
        error_string="«sávzzat",
        start=0,
        end=8,
        error_type="punct-aistton-left",
        explanation="Leat boasttuaisttonmearkkat.",
        suggestions=["“sávzzat"],
    )

    expected_fixed_error = ErrorData(
        error_string="«",
        start=0,
        end=1,
        error_type="punct-aistton-left",
        explanation="Leat boasttuaisttonmearkkat.",
        suggestions=["“"],
    )

    fixed_error = fix_aistton_left(input_error)

    assert fixed_error == expected_fixed_error


def test_remove_aistton():
    input_errors = [
        ErrorData(
            'sávzzat"',
            6,
            14,
            "punct-aistton",
            "Leat boasttuaisttonmearkkat.",
            ["sávzzatsávzzat”"],
        ),
        ErrorData(
            'sávzzat"',
            6,
            14,
            "punct-aistton-right",
            "Leat boasttuaisttonmearkkat.",
            ["sávzzatsávzzat”"],
        ),
    ]
    excepted_errors = [
        ErrorData(
            'sávzzat"',
            6,
            14,
            "punct-aistton-right",
            "Leat boasttuaisttonmearkkat.",
            ["sávzzatsávzzat”"],
        ),
    ]

    fixed_errors = remove_aistton(input_errors)

    assert fixed_errors == excepted_errors

@pytest.mark.parametrize(
    ("errors", "wanted_errors"),
    [
        (
            [
                ErrorData(
                    '"Goaskin viellja"',
                    15,
                    32,
                    "msyn-compound",
                    '"Goaskin viellja" orru leamen goallossátni',
                    ['"Goaskinviellja"'],
                ),
                ErrorData(
                    '"Goaskin viellja"',
                    15,
                    32,
                    "punct-aistton-both",
                    "Boasttuaisttonmearkkat",
                    ["”Goaskin viellja”"],
                ),
            ],
            [
                ErrorData(
                    "Goaskin viellja",
                    16,
                    31,
                    "msyn-compound",
                    '"Goaskin viellja" orru leamen goallossátni',
                    ["Goaskinviellja"],
                ),
                ErrorData(
                    '"Goaskin viellja"',
                    15,
                    32,
                    "punct-aistton-both",
                    "Boasttuaisttonmearkkat",
                    ["”Goaskin viellja”"],
                ),
            ],
        ),
        (
            [
                ErrorData(
                    "dálve olympiijagilvvuid",
                    22,
                    45,
                    "msyn-compound",
                    '"dálve olympiijagilvvuid" orru leamen goallossátni',
                    ["dálveolympiijagilvvuid"],
                ),
                ErrorData(
                    "CDa",
                    53,
                    56,
                    "typo",
                    "Ii leat sátnelisttus",
                    ["CD"],
                ),
                ErrorData(      
                    "“Dálveleaikat“",
                    78,
                    92,
                    "real-PlNomPxSg2-PlNom",
                    "Sátni šaddá eará go oaivvilduvvo",
                    ["“Dálveleaikkat“"],
                ),
                ErrorData(
                    "“Dálveleaikat“",
                    78,
                    92,
                    "punct-aistton-both",
                    "Boasttuaisttonmearkkat",
                    ["”Dálveleaikat”"],
                ),
            ],
            [
                ErrorData(
                    "dálve olympiijagilvvuid",
                    22,
                    45,
                    "msyn-compound",
                    '"dálve olympiijagilvvuid" orru leamen goallossátni',
                    ["dálveolympiijagilvvuid"],
                ),
                ErrorData(
                    "CDa",
                    53,
                    56,
                    "typo",
                    "Ii leat sátnelisttus",
                    ["CD"],
                ),
                ErrorData(
                    "Dálveleaikat",
                    79,
                    91,
                    "real-PlNomPxSg2-PlNom",
                    "Sátni šaddá eará go oaivvilduvvo",
                    ["Dálveleaikkat"],
                ),
                ErrorData(  
                    "“Dálveleaikat“",
                    78,
                    92,
                    "punct-aistton-both",
                    "Boasttuaisttonmearkkat",
                    ["”Dálveleaikat”"],
                ),
            ],
        ),
    ],
)
def test_fix_hidden_by_aistton_both(errors, wanted_errors):
    assert fix_hidden_by_aistton(errors) == wanted_errors
