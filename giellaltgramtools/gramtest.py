# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

from collections import Counter


class GramTest:

    def __init__(self):
        self.count = Counter()

    def run_tests(self):
        test_results = self.tests
        self.test_results = [
            self.run_test(test_number, test_result, len(test_results))
            for (test_number, test_result) in enumerate(test_results, start=1)
        ]

        self.config.get("out").final_result(self.count)

    def run_test(self, test_number, test_result, length):
        count = Counter()

        true_positives = self.has_true_positives(
            test_result["expected_errors"], test_result["gramcheck_errors"]
        )
        count["tp"] = len(true_positives)
        true_negatives = self.has_true_negatives(
            test_result["expected_errors"], test_result["gramcheck_errors"]
        )
        count["tn"] = len(true_negatives)
        false_positives_1 = self.has_false_positives_1(
            test_result["expected_errors"], test_result["gramcheck_errors"]
        )
        count["fp1"] = len(false_positives_1)
        false_positives_2 = self.has_false_positives_2(
            test_result["expected_errors"], test_result["gramcheck_errors"]
        )
        count["fp2"] = len(false_positives_2)
        false_negatives_1 = self.has_false_negatives_1(
            test_result["expected_errors"], test_result["gramcheck_errors"]
        )
        count["fn1"] = len(false_negatives_1)
        false_negatives_2 = self.has_false_negatives_2(
            test_result["expected_errors"], test_result["gramcheck_errors"]
        )
        count["fn2"] = len(false_negatives_2)

        has_fails = any(
            [false_negatives_1, false_negatives_2, false_positives_1, false_positives_2]
        )
        out = self.config.get("out")

        if not (self.config.get("hide_passes", False) and not has_fails):
            out.title(test_number, length, test_result["uncorrected"])

        if not self.config.get("hide_passes", False):
            for true_positive in true_positives:
                out.success(
                    test_number,
                    length,
                    "tp",
                    true_positive[0],
                    true_positive[1],
                    test_result["filename"],
                )

            for true_negative in true_negatives:
                out.success(
                    test_number,
                    length,
                    "tn",
                    true_negative[0],
                    true_negative[1],
                    test_result["filename"],
                )

        for false_positive_1 in false_positives_1:
            out.failure(
                test_number,
                length,
                "fp1",
                false_positive_1[0],
                false_positive_1[1],
                test_result["filename"],
            )

        expected_error = ["", "", "", "", "", ""]
        for false_positive_2 in false_positives_2:
            out.failure(
                test_number,
                length,
                "fp2",
                expected_error,
                false_positive_2,
                test_result["filename"],
            )

        for false_negative_1 in false_negatives_1:
            out.failure(
                test_number,
                length,
                "fn1",
                false_negative_1[0],
                false_negative_1[1],
                test_result["filename"],
            )

        gramcheck_error = ["", "", "", "", "", []]
        for false_negative_2 in false_negatives_2:
            out.failure(
                test_number,
                length,
                "fn2",
                false_negative_2,
                gramcheck_error,
                test_result["filename"],
            )

        if not (self.config.get("hide_passes", False) and not has_fails):
            out.result(test_number, count, test_result["uncorrected"])

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
        return list(self.paragraphs)
