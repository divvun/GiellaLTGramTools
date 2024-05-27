# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

from collections import Counter


class GramTest:

    def __init__(self):
        self.count = Counter()

    def run_tests(self):
        tests = self.tests
        self.test_results = [
            self.run_test(item, len(tests))
            for item in enumerate(tests.items(), start=1)
        ]

        self.config.get("out").final_result(self.count)

    def run_test(self, item, length):
        count = Counter()
        expected_errors = item[1][1]["expected_errors"]
        gramcheck_errors = item[1][1]["gramcheck_errors"]

        true_positives = self.has_true_positives(expected_errors, gramcheck_errors)
        count["tp"] = len(true_positives)
        true_negatives = self.has_true_negatives(expected_errors, gramcheck_errors)
        count["tn"] = len(true_negatives)
        false_positives_1 = self.has_false_positives_1(
            expected_errors, gramcheck_errors
        )
        count["fp1"] = len(false_positives_1)
        false_positives_2 = self.has_false_positives_2(
            expected_errors, gramcheck_errors
        )
        count["fp2"] = len(false_positives_2)
        false_negatives_1 = self.has_false_negatives_1(
            expected_errors, gramcheck_errors
        )
        count["fn1"] = len(false_negatives_1)
        false_negatives_2 = self.has_false_negatives_2(
            expected_errors, gramcheck_errors
        )
        count["fn2"] = len(false_negatives_2)

        has_fails = any(
            [false_negatives_1, false_negatives_2, false_positives_1, false_positives_2]
        )
        out = self.config.get("out")
        filename = item[1][1]["filename"]

        if not (self.config.get("hide_passes", False) and not has_fails):
            out.title(item[0], length, item[1][0])

        if not self.config.get("hide_passes", False):
            for true_positive in true_positives:
                out.success(
                    item[0], length, "tp", true_positive[0], true_positive[1], filename
                )

            for true_negative in true_negatives:
                out.success(
                    item[0], length, "tn", true_negative[0], true_negative[1], filename
                )

        for false_positive_1 in false_positives_1:
            out.failure(
                item[0],
                length,
                "fp1",
                false_positive_1[0],
                false_positive_1[1],
                filename,
            )

        expected_error = ["", "", "", "", "", ""]
        for false_positive_2 in false_positives_2:
            out.failure(
                item[0], length, "fp2", expected_error, false_positive_2, filename
            )

        for false_negative_1 in false_negatives_1:
            out.failure(
                item[0],
                length,
                "fn1",
                false_negative_1[0],
                false_negative_1[1],
                filename,
            )

        gramcheck_error = ["", "", "", "", "", []]
        for false_negative_2 in false_negatives_2:
            out.failure(
                item[0], length, "fn2", false_negative_2, gramcheck_error, filename
            )

        if not (self.config.get("hide_passes", False) and not has_fails):
            out.result(item[0], count, item[1][0])

        for key in count:
            self.count[key] += count[key]

        # Did this test sentence as a whole pass or not
        return not has_fails

    def has_same_range_and_error(self, c_error, d_error):
        """Check if the errors have the same range and error"""
        if d_error[3] == "double-space-before":
            return c_error[1:2] == d_error[1:2]
        else:
            return c_error[:3] == d_error[:3]

    def has_suggestions_with_hit(self, c_error, d_error):
        """Check if markup error correction exists in grammarchecker error."""
        return (
            len(d_error[5]) > 0
            and self.has_same_range_and_error(c_error, d_error)
            and any(correct in d_error[5] for correct in c_error[5])
        )

    def has_true_negatives(self, correct, dc):
        if not correct and not dc:
            return [(["", "", "", "", "", ""], ["", "", "", "", "", ""])]

        return []

    def has_true_positives(self, correct, dc):
        return [
            (c_error, d_error)
            for c_error in correct
            for d_error in dc
            if self.has_suggestions_with_hit(c_error, d_error)
        ]

    def has_false_positives_1(self, correct, dc):
        return [
            (c_error, d_error)
            for c_error in correct
            for d_error in dc
            if self.has_suggestions_without_hit(c_error, d_error)
        ]

    def has_suggestions_without_hit(self, c_error, d_error):
        return (
            self.has_same_range_and_error(c_error, d_error)
            and d_error[5]
            and not any(correct in d_error[5] for correct in c_error[5])
        )

    def has_false_positives_2(self, correct, dc):
        return [
            d_error
            for d_error in dc
            if not any(
                self.has_same_range_and_error(c_error, d_error) for c_error in correct
            )
        ]

    def has_false_negatives_2(self, c_errors, d_errors):
        corrects = []
        for c_error in c_errors:
            for d_error in d_errors:
                if self.has_same_range_and_error(c_error, d_error):
                    break
            else:
                corrects.append(c_error)

        return corrects

    def has_false_negatives_1(self, correct, dc):
        return [
            (c_error, d_error)
            for c_error in correct
            for d_error in dc
            if self.has_no_suggestions(c_error, d_error)
        ]

    def has_no_suggestions(self, c_error, d_error):
        return self.has_same_range_and_error(c_error, d_error) and not d_error[5]

    def run(self):
        self.run_tests()

        return 0 if all(self.test_results) else 1

    def __str__(self):
        return str(self.config.get("out"))

    @property
    def tests(self):
        return {test["uncorrected"]: test for test in self.paragraphs}
