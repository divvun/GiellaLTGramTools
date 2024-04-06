# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

import json
import subprocess


class GramChecker:
    def __init__(self, ignore_typos=False):
        self.ignore_typos = ignore_typos

    def check_paragraphs(self, paragraphs):
        """Check grammar of a paragraphs."""
        result = subprocess.run(
            self.checker.split(),
            input=paragraphs.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        lines = result.stdout.decode("utf-8").strip().split("\n")
        return [
            gram_error.get("errs") for gram_error in json.loads(f"[{','.join(lines)}]")
        ]

    @staticmethod
    def remove_dupes(double_spaces, d_errors):
        for removable_error in [
            d_error
            for double_space in double_spaces
            for d_error in d_errors
            if double_space[1:2] == d_error[1:2]
        ]:
            d_errors.remove(removable_error)

    @staticmethod
    def sort_by_range(error):
        return error[1:2]

    def add_part(self, part, start, end, d_errors):
        res = self.check_grammar(part)
        errors = res["errs"]
        for error in [error for error in errors if error]:
            candidate = [error[0], start, end, error[3], error[4], error[5], error[6]]
            if candidate not in d_errors:
                d_errors.append(candidate)

    def fix_no_space_before_parent_start(self, space_error, d_errors):
        for dupe in [
            d_error for d_error in d_errors if d_error[1:2] == space_error[1:2]
        ]:
            d_errors.remove(dupe)

        parenthesis = space_error[0].find("(")
        d_errors.append(
            [
                space_error[0][parenthesis:],
                space_error[1] + parenthesis,
                space_error[2],
                space_error[3],
                space_error[4],
                [" ("],
                space_error[6],
            ]
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

    def fix_aistton_left(self, d_error, d_errors, position):
        sentence = d_error[0][1:]
        d_error[0] = d_error[0][0]
        d_error[5] = ["”"]
        d_error[2] = d_error[1] + 1

        res = self.check_grammar(sentence)
        new_d_error = res["errs"]
        if new_d_error:
            new_d_error[0][1] = d_error[1] + 1
            new_d_error[0][2] = d_error[1] + 1 + len(sentence)
            d_errors.insert(position + 1, new_d_error[0])

    def fix_aistton_right(self, d_error, d_errors, position):
        sentence = d_error[0][:-1]
        d_error[0] = d_error[0][-1]
        d_error[5] = ["”"]
        d_error[1] = d_error[2] - 1

        res = self.check_grammar(sentence)
        new_d_error = res["errs"]
        if new_d_error:
            new_d_error[0][1] = d_error[1] - len(sentence)
            new_d_error[0][2] = d_error[1]
            d_errors.insert(position, new_d_error[0])

    def fix_hidden_by_aistton_both(self, d_errors):
        """Make the index, error and suggestions match the manual errormarkup."""

        def is_hidden_error(error):
            return (error[1], error[2]) in aistton_both_ranges and error[
                3
            ] != "punct-aistton-both"

        def fix_hidden_error(error):
            return [
                error[0][1:-1],
                error[1] + 1,
                error[2] - 1,
                error[3],
                error[4],
                [suggestion[1:-1] for suggestion in error[5]],
            ]

        aistton_both_ranges = [
            (error[1], error[2])
            for error in d_errors
            if error[3] == "punct-aistton-both"
        ]
        return [
            fix_hidden_error(error) if is_hidden_error(error) else error
            for error in d_errors
        ]

    def fix_aistton_both(self, d_error, d_errors, position):
        if d_error[0][-1] != "”":
            right_error = list(d_error)
            right_error[0] = right_error[0][-1]
            right_error[5] = ["”"]
            right_error[1] = right_error[2] - 1
            right_error[3] = "punct-aistton-both"
            d_errors.insert(position + 1, right_error)

        d_error[0] = d_error[0][0]
        d_error[5] = ["”"]
        d_error[2] = d_error[1] + 1

    def fix_aistton(self, d_errors):
        aistton_fixers = {
            "punct-aistton-left": self.fix_aistton_left,
            "punct-aistton-right": self.fix_aistton_right,
            "punct-aistton-both": self.fix_aistton_both,
        }

        for position, d_error in enumerate(d_errors):
            if (
                d_error[3] in aistton_fixers
                and len(d_error[0]) > 1
                and len(d_error[5]) == 1
            ):
                aistton_fixers[d_error[3]](d_error, d_errors, position)

    def get_error_corrections(self, para):
        parts = []
        if para.text is not None:
            parts.append(para.text)
        for child in para:
            if child.tag != "correct":
                correct = child.find("./correct")
                parts.append(correct.text if correct.text is not None else "")
                for grandchild in child:
                    if grandchild.tag != "correct":
                        parts.append(self.get_error_corrections(grandchild))

        if not len(para) and para.tail:
            parts.append(para.tail)

        return "".join(parts)

    @staticmethod
    def is_non_nested_error(para):
        """Check if the only children are correct elements."""
        return all(child.tag == "correct" for child in para)

    def extract_error_info(self, parts, errors, para):
        """Only collect unnested errors."""
        info = ["", "", "", "", "", ""]
        if para.tag.startswith("error"):
            info[0] = self.get_error_corrections(para) if len(para) else para.text
            info[1] = len("".join(parts))
            info[3] = para.tag
            correct = para.find("./correct")
            info[4] = correct.attrib.get("errorinfo", default="")
            info[5] = [
                correct.text if correct.text is not None else ""
                for correct in para.xpath("./correct")
            ]

        if para.text:
            parts.append(para.text)

        for child in para:
            if child.tag != "correct":
                if self.is_non_nested_error(child):
                    errors.append(self.extract_error_info(parts, errors, child))
                else:
                    self.extract_error_info(parts, errors, child)

        if para.tag.startswith("error"):
            info[2] = len("".join(parts))

        if para.tail:
            parts.append(para.tail)

        return info

    def fix_all_errors(self, d_errors):
        """Remove errors that cover the same area of the typo and msyn types."""

        def report_dupes(errors):
            found_errors = set()
            index_set = set()
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

            for pos in sorted(index_set, reverse=True):
                del errors[pos]

        d_errors = self.fix_hidden_by_aistton_both(d_errors)
        self.fix_aistton(d_errors)
        for d_error in d_errors:
            if d_error[3] == "no-space-before-parent-start":
                self.fix_no_space_before_parent_start(d_error, d_errors)

        report_dupes(d_errors)

        return d_errors

    def check_sentence(self, sentence):
        res = self.check_grammar(sentence)

        return self.fix_all_errors(res["errs"])

    def normalise_error_markup(self, errors):
        for error in errors:
            if (
                error[3] == "errorformat"
                and error[4] == "notspace"
                and "  " in error[0]
            ):
                d_pos = error[0].find("  ")
                error[1] = error[1] + d_pos
                error[2] = error[1] + 3
                error[0] = error[0][error[1] : error[2]]

    def normalise_grammar_markup(self, errors):
        for error in errors:
            if error[3] == "double-space-before":
                d_pos = error[0].find("  ")
                error[1] = error[1] + d_pos
                error[2] = error[1] + 3
                error[0] = error[0][error[1] : error[2]]

    def remove_non_hits(self, errors, d_errors):
        """Find the d_errors that correspond with errors."""
        return [
            d_error
            for error in errors
            for d_error in d_errors
            if d_error[1:2] == error[1:2]
        ]

    def paragraph_to_testdata(self, para):
        """Extract sentence and markup errors."""
        parts = []
        errors = []
        self.extract_error_info(parts, errors, para)
        self.normalise_error_markup(errors)

        sentence = "".join(parts)

        return sentence, errors

    def remove_foreign(self, marked_errors, found_errors):
        """Remove foreign language error elements."""
        foreign_ranges = [
            (marked_error[1], marked_error[2])
            for marked_error in marked_errors
            if marked_error[3] == "errorlang"
        ]
        return (
            [
                marked_error
                for marked_error in marked_errors
                if marked_error[3] != "errorlang"
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

    def remove_typo(self, marked_errors, found_errors):
        """Remove foreign language error elements."""
        return (
            [
                marked_error
                for marked_error in marked_errors
                if marked_error[3] != "errorort"
            ],
            [found_error for found_error in found_errors if found_error[3] != "typo"],
        )

    def clean_data(self, sentence, expected_errors, gramcheck_errors, filename):
        """Extract data for reporting from a paragraph."""
        self.normalise_grammar_markup(gramcheck_errors)
        expected_errors, gramcheck_errors = self.remove_foreign(
            expected_errors, gramcheck_errors
        )
        if self.ignore_typos:
            expected_errors, gramcheck_errors = self.remove_typo(
                expected_errors, gramcheck_errors
            )

        return {
            "uncorrected": sentence,
            "expected_errors": expected_errors,
            "gramcheck_errors": gramcheck_errors,
            "filename": filename,
        }