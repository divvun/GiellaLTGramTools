# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
import multiprocessing
import subprocess
from functools import partial
from typing import Iterator

from giellaltgramtools.errordata import ErrorData
from giellaltgramtools.grammar_error_annotated_sentence import (
    GrammarErrorAnnotatedSentence,
    divvun_checker_to_grammar_error_annotated_sentences,
)
from giellaltgramtools.runtime_parser import (
    runtime_to_grammar_error_annotated_sentences,
)
from giellaltgramtools.testdata import TestData


def check_paragraphs(
    command: str, paragraphs: list[str]
) -> list[GrammarErrorAnnotatedSentence]:
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
    return (
        runtime_to_grammar_error_annotated_sentences(output)
        if "divvun-runtime" in command
        else divvun_checker_to_grammar_error_annotated_sentences(output)
    )


def chunks(lst: list[str], n: int) -> Iterator[list[str]]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def check_paragraphs_in_parallel(
    command: str, paragraphs: list[str]
) -> list[GrammarErrorAnnotatedSentence]:
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
        grammar_chunks = pool.map(with_command, chunked_data)

    return [item for sublist in grammar_chunks for item in sublist]


class GramChecker:
    def __init__(self, ignore_typos: bool = False):
        self.ignore_typos = ignore_typos
        self.checker = ""

    def remove_foreign(
        self,
        marked_errors: tuple[ErrorData, ...],
        found_errors: tuple[ErrorData, ...],
    ) -> tuple[tuple[ErrorData, ...], tuple[ErrorData, ...]]:
        """Remove foreign language error elements."""
        foreign_ranges = [
            (marked_error.start, marked_error.end)
            for marked_error in marked_errors
            if marked_error.error_type == "errorlang"
        ]
        return (
            tuple(

                marked_error
                for marked_error in marked_errors
                if marked_error.error_type != "errorlang"
            ),
            tuple(

                found_error
                for found_error in found_errors
                if not any(
                    foreign_range[0] <= found_error.start < foreign_range[1]
                    and found_error.end <= foreign_range[1]
                    for foreign_range in foreign_ranges
                )
            ),
        )

    def remove_typo(
        self,
        marked_errors: tuple[ErrorData, ...],
        found_errors: tuple[ErrorData, ...],
    ) -> tuple[tuple[ErrorData, ...], tuple[ErrorData, ...]]:
        """Remove typos from test material."""
        return (
            tuple(

                marked_error
                for marked_error in marked_errors
                if marked_error.error_type != "errorort"
            ),
            tuple(

                found_error
                for found_error in found_errors
                if found_error.error_type != "typo"
            ),
        )

    def clean_data(
        self,
        sentence: str,
        expected_errors: tuple[ErrorData, ...],
        gramcheck_errors: tuple[ErrorData, ...],
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
