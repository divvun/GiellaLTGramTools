# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
import json
import multiprocessing
import subprocess
from functools import partial
from typing import Iterator

from giellaltgramtools.errordata import ErrorData, divvun_checker_to_error_data
from giellaltgramtools.grammar_error_annotated_sentence import (
    GrammarErrorAnnotatedSentence,
)
from giellaltgramtools.runtime_parser import runtime_output_to_checker_json_lines
from giellaltgramtools.testdata import TestData


def check_paragraphs(command: str, paragraphs: list[str]) -> str:
    """Check grammar of paragraphs.

    Args:
        command (str): Command to run (divvun-checker or divvun-runtime)
        paragraphs (str): Lines split by newlines.
            The grammarchecker checks each line separately.
    Returns:
        str: String version of grammarchecker output in divvun-checker format.
    """
    result = subprocess.run(
        command.split(),
        input="\n".join(paragraphs).encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    output = result.stdout.decode("utf-8")

    # If using divvun-runtime, convert output to divvun-checker format
    if "divvun-runtime" in command:
        output = runtime_output_to_checker_json_lines(output)

    return output


def chunks(lst: list[str], n: int) -> Iterator[list[str]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def check_paragraphs_in_parallel(command: str, paragraphs: list[str]) -> str:
    """Check grammar of paragraphs in parallel.

    Args:
        command (str): Command to run (divvun-checker or divvun-runtime)
        paragraphs (list): List of paragraphs.
    Returns:
        str: String version of grammarchecker outputs in divvun-checker format.
    """
    with_command = partial(check_paragraphs, command)
    num_processes = multiprocessing.cpu_count()
    chunked_data = list(chunks(paragraphs, 10))

    with multiprocessing.Pool(processes=num_processes) as pool:
        strings = pool.map(with_command, chunked_data)

    return "".join(strings)


def sort_by_range(
    error: tuple[str, int, int, str, str, list[str], str],
) -> list[int]:
    return list(error[1:3])


def fix_paragraphs(
    command: str,
    result_str: str,
) -> list[GrammarErrorAnnotatedSentence]:
    """Fix grammar of a paragraphs.

    Args:
        result_str: Gramcheck output as a string.
            Each line is a JSON object containing the grammar checker's
            result of a single paragraph.
    Returns:
        list: List of tuples containing input sentence and error data.
    """
    lines = result_str.strip().split("\n")
    return [
        GrammarErrorAnnotatedSentence(
            sentence=gram_error.get("text"),
            errors=[
                divvun_checker_to_error_data(fixed_error)
                for fixed_error in fix_all_errors(command, gram_error.get("errs"))
            ],
        )
        for gram_error in json.loads(f"[{','.join(lines)}]")
    ]


def fix_all_errors(
    command: str,
    d_errors: list[tuple[str, int, int, str, str, list[str], str]],
) -> list[tuple[str, int, int, str, str, list[str], str]]:
    """Remove errors that cover the same area of the typo and msyn types."""
    d_errors = list(fix_aistton(d_errors))
    remove_duplicate_errors(d_errors)
    return d_errors


def add_part(
    command: str,
    part: str,
    start: int,
    end: int,
    d_errors: list[tuple[str, int, int, str, str, list[str], str]],
) -> None:
    res = check_paragraphs(command, [part])
    res_as_dict = json.loads(res.strip())
    errors: list[tuple[str, int, int, str, str, list[str], str]] = res_as_dict["errs"]
    for error in [error for error in errors if error]:
        candidate: tuple[str, int, int, str, str, list[str], str] = (
            error[0],
            start,
            end,
            error[3],
            error[4],
            error[5],
            error[6],
        )
        if candidate not in d_errors:
            d_errors.append(candidate)


def fix_hidden_by_aistton(
    d_errors: list[tuple[str, int, int, str, str, list[str], str]],
) -> list[tuple[str, int, int, str, str, list[str], str]]:
    """Fix errors hidden by aistton-both errors.

    A GramDivvun error of type aistton-both can contain some other error.
    The other error is reported as having the same range as the aistton-both error.

    This function fixes the range to match the marked up error.

    Args:
        d_errors (list): List of GramDivvun errors.

    Returns:
        list: List of GramDivvun errors with the hidden errors revealed.
    """

    def is_hidden_error(
        error: tuple[str, int, int, str, str, list[str], str],
    ) -> bool:
        return (error[1], error[2]) in aistton_ranges and error[3] not in [
            "punct-aistton-both",
            "punct-aistton-left",
            "punct-aistton-right",
        ]

    def fix_hidden_error(
        error: tuple[str, int, int, str, str, list[str], str],
    ) -> tuple[str, int, int, str, str, list[str], str]:
        if error[3] == "punct-aistton-left":
            return (
                error[0][1:],
                error[1] + 1,
                error[2],
                error[3],
                error[4],
                [suggestion[1:] for suggestion in error[5]],
                error[6],
            )
        if error[3] == "punct-aistton-right":
            return (
                error[0][:-1],
                error[1],
                error[2] - 1,
                error[3],
                error[4],
                [suggestion[:-1] for suggestion in error[5]],
                error[6],
            )

        return (
            error[0][1:-1],
            error[1] + 1,
            error[2] - 1,
            error[3],
            error[4],
            [suggestion[1:-1] for suggestion in error[5]],
            error[6],
        )

    aistton_ranges = [
        (error[1], error[2])
        for error in d_errors
        if error[3]
        in ["punct-aistton-both", "punct-aistton-left", "punct-aistton-right"]
    ]
    return [
        fix_hidden_error(error) if is_hidden_error(error) else error
        for error in d_errors
    ]


def fix_aistton(
    d_errors: list[tuple[str, int, int, str, str, list[str], str]],
) -> Iterator[tuple[str, int, int, str, str, list[str], str]]:
    """Rearrange GramDivvun aistton errors to match the Giella markup format.

    GramDivvun marks up errors with wrong quotemarks by including the word next to
    the quote marks.

    The manual error markup, on the other hand, only marks up the quote marks.

    Args:
        d_errors (list): List of GramDivvun errors.
    Returns:
        list: List of GramDivvun errors with aistton errors fixed.
    """
    for d_error in fix_hidden_by_aistton(d_errors):
        # Skip punct-aistton errors
        # punct-aistton are emitted together with
        # punct-aistton-left and punct-aistton-right
        if d_error[3] != "punct-aistton":
            if d_error[3] == "punct-aistton-both":
                yield (
                    d_error[0][0],
                    d_error[1],
                    d_error[1] + 1,
                    d_error[3],
                    d_error[4],
                    ["”"],
                    d_error[6],
                )
                yield (
                    d_error[0][-1],
                    d_error[2] - 1,
                    d_error[2],
                    d_error[3],
                    d_error[4],
                    ["”"],
                    d_error[6],
                )
            elif d_error[3] == "punct-aistton-left":
                yield (
                    d_error[0][0],
                    d_error[1],
                    d_error[1] + 1,
                    d_error[3],
                    d_error[4],
                    ["”"],
                    d_error[6],
                )
            elif d_error[3] == "punct-aistton-right":
                yield (
                    d_error[0][-1],
                    d_error[2] - 1,
                    d_error[2],
                    d_error[3],
                    d_error[4],
                    ["”"],
                    d_error[6],
                )
            else:
                yield d_error


def find_duplicate_errors(
    errors: list[tuple[str, int, int, str, str, list[str], str]],
) -> set[int]:
    """Find indices of duplicate errors that should be removed."""
    found_errors: set[str] = set()
    index_set: set[int] = set()

    for error1 in errors:
        for error2 in errors:
            if error1[:3] == error2[:3] and error1 != error2:
                if str(error1) not in found_errors and str(error2) not in found_errors:
                    found_errors.add(str(error1))
                    found_errors.add(str(error2))
                    index_set.add(errors.index(error1))

    return index_set


def remove_duplicate_errors(
    errors: list[tuple[str, int, int, str, str, list[str], str]],
) -> None:
    """Remove duplicate errors from the list."""
    duplicate_indices = find_duplicate_errors(errors)
    for pos in sorted(duplicate_indices, reverse=True):
        del errors[pos]


class GramChecker:
    def __init__(self, ignore_typos: bool = False):
        self.ignore_typos = ignore_typos
        self.checker = ""

    def remove_foreign(
        self,
        marked_errors: list[ErrorData],
        found_errors: list[ErrorData],
    ) -> tuple[list[ErrorData], list[ErrorData]]:
        """Remove foreign language error elements."""
        foreign_ranges = [
            (marked_error.start, marked_error.end)
            for marked_error in marked_errors
            if marked_error.error_type == "errorlang"
        ]
        return (
            [
                marked_error
                for marked_error in marked_errors
                if marked_error.error_type != "errorlang"
            ],
            [
                found_error
                for found_error in found_errors
                if not any(
                    foreign_range[0] <= found_error.start < foreign_range[1]
                    and found_error.end <= foreign_range[1]
                    for foreign_range in foreign_ranges
                )
            ],
        )

    def remove_typo(
        self,
        marked_errors: list[ErrorData],
        found_errors: list[ErrorData],
    ) -> tuple[list[ErrorData], list[ErrorData]]:
        """Remove foreign language error elements."""
        return (
            [
                marked_error
                for marked_error in marked_errors
                if marked_error.error_type != "errorort"
            ],
            [
                found_error
                for found_error in found_errors
                if found_error.error_type != "typo"
            ],
        )

    def clean_data(
        self,
        sentence: str,
        expected_errors: list[ErrorData],
        gramcheck_errors: list[ErrorData],
        filename: str,
    ) -> TestData:
        """Extract data for reporting from a paragraph."""
        expected_errors, gramcheck_errors = self.remove_foreign(
            expected_errors, gramcheck_errors
        )
        if self.ignore_typos:
            expected_errors, gramcheck_errors = self.remove_typo(
                expected_errors, gramcheck_errors
            )

        return TestData(
            uncorrected=sentence,
            expected_errors=expected_errors,
            gramcheck_errors=gramcheck_errors,
            filename=filename,
        )
