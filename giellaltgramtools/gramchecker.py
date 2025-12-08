# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

import json
import multiprocessing
import subprocess
from functools import partial
from typing import Iterator

from lxml.etree import _Element  # pyright: ignore[reportPrivateUsage]

from giellaltgramtools.errordata import ErrorData
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
        check=True,
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


class GramChecker:
    def __init__(self, ignore_typos: bool = False):
        self.ignore_typos = ignore_typos
        self.checker = ""

    def fix_paragraphs(
        self, result_str: str
    ) -> list[tuple[str, list[list[tuple[str, int, int, str, str, list[str], str]]]]]:
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
            (gram_error.get("text"), self.fix_all_errors(gram_error.get("errs")))
            for gram_error in json.loads(f"[{','.join(lines)}]")
        ]

    @staticmethod
    def sort_by_range(
        error: tuple[str, int, int, str, str, list[str], str],
    ) -> list[int]:
        return list(error[1:3])

    def add_part(
        self,
        part: str,
        start: int,
        end: int,
        d_errors: list[tuple[str, int, int, str, str, list[str], str]],
    ) -> None:
        res = check_paragraphs(self.checker, [part])
        res_as_dict = json.loads(res.strip())
        errors: list[tuple[str, int, int, str, str, list[str], str]] = res_as_dict[
            "errs"
        ]
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

    def fix_no_space_before_parent_start(
        self,
        space_error: tuple[str, int, int, str, str, list[str], str],
        d_errors: list[tuple[str, int, int, str, str, list[str], str]],
    ) -> None:
        for dupe in [
            d_error for d_error in d_errors if d_error[1:3] == space_error[1:3]
        ]:
            d_errors.remove(dupe)

        parenthesis = space_error[0].find("(")
        d_errors.append(
            (
                space_error[0][parenthesis:],
                space_error[1] + parenthesis,
                space_error[2],
                space_error[3],
                space_error[4],
                [" ("],
                space_error[6],
            )
        )
        part1 = space_error[0][:parenthesis]
        start = space_error[1]
        end = space_error[1] + len(part1)
        if part1:
            self.add_part(part1, start, end, d_errors)

        part2 = space_error[0][parenthesis + 1 :]
        start = space_error[1] + parenthesis + 1
        end = space_error[1] + parenthesis + 1 + len(part2)
        if part2:
            self.add_part(part2, start, end, d_errors)

        d_errors.sort(key=self.sort_by_range)

    def fix_hidden_by_aistton(
        self, d_errors: list[tuple[str, int, int, str, str, list[str], str]]
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
        self, d_errors: list[tuple[str, int, int, str, str, list[str], str]]
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
        for d_error in self.fix_hidden_by_aistton(d_errors):
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

    def get_error_corrections(self, para: _Element) -> str:
        parts: list[str] = []
        if para.text is not None:
            parts.append(para.text)
        for child in para:
            if child.tag != "correct":
                correct = child.find("./correct")
                if correct is not None:
                    parts.append(correct.text if correct.text is not None else "")
                    for grandchild in child:
                        if grandchild.tag != "correct":
                            parts.append(self.get_error_corrections(grandchild))

        if not len(para) and para.tail:
            parts.append(para.tail)

        return "".join(parts)

    @staticmethod
    def is_non_nested_error(para: _Element) -> bool:
        """Check if the only children are correct elements."""
        return all(child.tag == "correct" for child in para)

    def extract_error_info(
        self, parts: list[str], errors: list[ErrorData | None], para: _Element
    ) -> ErrorData | None:
        """Only collect unnested errors."""
        info = None

        if para.tag.startswith("error"):
            correct = para.find("./correct")
            info = ErrorData(
                error_string=(
                    self.get_error_corrections(para) if len(para) else (para.text or "")
                ),
                start=len("".join(parts)),
                end=-1,  # Will be set later
                error_type=para.tag,
                explanation=(
                    correct.attrib.get("errorinfo", default="")
                    if correct is not None
                    else ""
                ),
                suggestions=[
                    correct.text if correct.text is not None else ""
                    for correct in para.xpath("./correct")
                ],
                native_error_type=para.tag,
            )

        if para.text:
            parts.append(para.text)

        for child in para:
            if child.tag != "correct":
                if self.is_non_nested_error(child):
                    errors.append(self.extract_error_info(parts, errors, child))
                else:
                    self.extract_error_info(parts, errors, child)

        # Now there is enough information to set the end position
        if info is not None and para.tag.startswith("error"):
            info.end = len("".join(parts))

        if para.tail:
            parts.append(para.tail)

        return info

    def _find_duplicate_errors(
        self, errors: list[tuple[str, int, int, str, str, list[str], str]]
    ) -> set[int]:
        """Find indices of duplicate errors that should be removed."""
        found_errors: set[str] = set()
        index_set: set[int] = set()

        for error1 in errors:
            for error2 in errors:
                if error1[:3] == error2[:3] and error1 != error2:
                    if (
                        str(error1) not in found_errors
                        and str(error2) not in found_errors
                    ):
                        found_errors.add(str(error1))
                        found_errors.add(str(error2))
                        index_set.add(errors.index(error1))

        return index_set

    def _remove_duplicate_errors(
        self, errors: list[tuple[str, int, int, str, str, list[str], str]]
    ) -> None:
        """Remove duplicate errors from the list."""
        duplicate_indices = self._find_duplicate_errors(errors)
        for pos in sorted(duplicate_indices, reverse=True):
            del errors[pos]

    def _process_special_errors(
        self, d_errors: list[tuple[str, int, int, str, str, list[str], str]]
    ) -> None:
        """Process special error types that need custom handling."""
        for d_error in d_errors:
            if d_error[3] == "no-space-before-parent-start":
                self.fix_no_space_before_parent_start(d_error, d_errors)

    def fix_all_errors(
        self, d_errors: list[tuple[str, int, int, str, str, list[str], str]]
    ) -> list[tuple[str, int, int, str, str, list[str], str]]:
        """Remove errors that cover the same area of the typo and msyn types."""
        d_errors = list(self.fix_aistton(d_errors))
        self._process_special_errors(d_errors)
        self._remove_duplicate_errors(d_errors)
        return d_errors

    def paragraph_to_testdata(self, para: _Element) -> tuple[str, list[ErrorData]]:
        """Extract sentence and markup errors."""
        parts: list[str] = []
        errors: list[ErrorData | None] = []
        self.extract_error_info(parts, errors, para)

        sentence = "".join(parts).replace("\n", " ")

        return sentence, [error for error in errors if error is not None]

    def remove_foreign(
        self,
        marked_errors: list[ErrorData],
        found_errors: list[tuple[str, int, int, str, str, list[str], str]],
    ):
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
                    foreign_range[0] <= found_error[1] < foreign_range[1]
                    and found_error[2] <= foreign_range[1]
                    for foreign_range in foreign_ranges
                )
            ],
        )

    def remove_typo(
        self,
        marked_errors: list[ErrorData],
        found_errors: list[tuple[str, int, int, str, str, list[str], str]],
    ) -> tuple[list[ErrorData], list[tuple[str, int, int, str, str, list[str], str]]]:
        """Remove foreign language error elements."""
        return (
            [
                marked_error
                for marked_error in marked_errors
                if marked_error.error_type != "errorort"
            ],
            [found_error for found_error in found_errors if found_error[3] != "typo"],
        )

    def clean_data(
        self,
        sentence: str,
        expected_errors: list[ErrorData],
        gramcheck_errors: list[tuple[str, int, int, str, str, list[str], str]],
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
            gramcheck_errors=[
                ErrorData(
                    error_string=gramcheck_error[0],
                    start=gramcheck_error[1],
                    end=gramcheck_error[2],
                    error_type=gramcheck_error[3],
                    explanation=gramcheck_error[4],
                    suggestions=gramcheck_error[5],
                    native_error_type=gramcheck_error[6],
                )
                for gramcheck_error in gramcheck_errors
            ],
            filename=filename,
        )
