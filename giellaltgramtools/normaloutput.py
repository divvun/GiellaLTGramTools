# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
from giellaltgramtools.alloutput import AllOutput
from giellaltgramtools.common import colourise


def light_blue(text: str) -> str:
    return colourise("{light_blue}" + text + "{reset}")


def green(text: str) -> str:
    return colourise("{green}" + text + "{reset}")


def blue(text: str) -> str:
    return colourise("{blue}" + text + "{reset}")


def red(text: str) -> str:
    return colourise("{red}" + text + "{reset}")


class NormalOutput(AllOutput):
    def title(self, index, length, test_case):
        self.write(f'{colourise("{light_blue}")}')
        self.write("-" * 10)
        self.write(f"\nTest {index}/{length}: {test_case}\n")
        self.write("-" * 10)
        self.write(f'{colourise("{reset}")}\n')

    def success(  # noqa: PLR0913
        self,
        test_number,
        number_of_tests,
        error_type,
        expected_error,
        gramcheck_error,
        filename,
    ):
        explanation = (
            f" ({expected_error.explanation})" if expected_error.explanation else ""
        )

        self.write(
            filename + "\n"
            "["
            + light_blue(f"{test_number}/{number_of_tests}")
            + "["
            + green(f"PASS {error_type}")
            + "] "
            + (
                (
                    f"{expected_error.error_string}:"
                    f"({', '.join(expected_error.suggestions)}"
                    f"{explanation}"
                    ")"
                )
                if expected_error.error_string
                else "No errors expected"
            )
            + " "
            + blue("=>")
            + " "
            + (
                (
                    f"{gramcheck_error.error_string}:"
                    f"[{', '.join(gramcheck_error.suggestions)}] "
                    f"({gramcheck_error.error_type})"
                )
                if gramcheck_error.error_string
                else "GramDivvun did not find any errors"
            )
            + "\n"
        )

    def failure(  # noqa: PLR0913
        self,
        test_number,
        number_of_tests,
        error_type,
        expected_error,
        gramcheck_error,
        filename,
    ):
        explanation = (
            f" ({expected_error.explanation})" if expected_error.explanation else ""
        )
        self.write(
            filename + "\n"
            "["
            + light_blue(f"{test_number}/{number_of_tests}")
            + "["
            + red(f"FAIL {error_type}")
            + "] "
            + (
                (
                    f"{expected_error.error_string}:"
                    f"({', '.join(expected_error.suggestions)})"
                    f"{explanation}"
                )
                if expected_error.error_string
                else "No errors expected"
            )
            + " "
            + blue("=>")
            + " "
            + (
                (
                    f"{gramcheck_error.error_string}:"
                    f"[{', '.join(gramcheck_error.suggestions)}] "
                    f"({gramcheck_error.error_type})"
                )
                if gramcheck_error.error_string
                else "GramDivvun did not find any errors"
            )
            + "\n"
        )

    def result(self, number, count, test_case):
        passes = sum([count[key] for key in count if key.startswith("t")])
        fails = sum([count[key] for key in count if key.startswith("f")])
        text = colourise(
            "Test {number} - Passes: {green}{passes}{reset}, "
            + "Fails: {red}{fails}{reset}, "
            + "Total: {light_blue}{total}{reset}\n\n",
            number=number,
            passes=passes,
            fails=fails,
            total=passes + fails,
        )
        self.write(text)

    def final_result(self, count):
        passes = sum([count[key] for key in count if key.startswith("t")])
        fails = sum([count[key] for key in count if key.startswith("f")])
        self.write(
            colourise(
                "Total passes: {green}{passes}{reset}, "
                + "Total fails: {red}{fails}{reset}, "
                + "Total: {light_blue}{total}{reset}\n",
                passes=passes,
                fails=fails,
                total=fails + passes,
            )
        )
        self.precision(count)

    def precision(self, count):
        try:
            true_positives = count["tp"]
            false_positives = count["fp1"] + count["fp2"]
            false_negatives = count["fn1"] + count["fn2"]

            prec = true_positives / (true_positives + false_positives)
            recall = true_positives / (true_positives + false_negatives)
            f1score = 2 * prec * recall / (prec + recall)

            self.write(
                colourise(
                    "True positive: {green}{true_positive}{reset}\n"
                    + "True negative: {green}{true_negative}{reset}\n"
                    + "False positive 1: {red}{fp1}{reset}\n"
                    + "False positive 2: {red}{fp2}{reset}\n"
                    + "False negative 1: {red}{fn1}{reset}\n"
                    + "False negative 2: {red}{fn2}{reset}\n"
                    + "Precision: {prec:.1f}%\n"
                    + "Recall: {recall:.1f}%\n"
                    + "F₁ score: {f1score:.1f}%\n",
                    true_positive=count["tp"],
                    true_negative=count["tn"],
                    fp1=count["fp1"],
                    fp2=count["fp2"],
                    fn1=count["fn1"],
                    fn2=count["fn2"],
                    prec=prec * 100,
                    recall=recall * 100,
                    f1score=f1score * 100,
                )
            )
        except ZeroDivisionError:
            pass
