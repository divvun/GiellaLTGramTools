# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

from collections import Counter
from io import StringIO

from giellaltgramtools.common import colourise


class GramTest:
    class AllOutput:
        def __init__(self, args):
            self._io = StringIO()
            self.args = args

        def __str__(self):
            return self._io.getvalue()

        def write(self, data):
            self._io.write(data)

        def info(self, data):
            self.write(data)

        def title(self, *args):
            pass

        def success(self, *args):
            pass

        def failure(self, *args):
            pass

        def false_positive_1(self, *args):
            pass

        def result(self, *args):
            pass

        def final_result(self, count):
            passes = count["tp"]
            fails = sum([count[key] for key in count if key != "tp"])
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

    class NormalOutput(AllOutput):
        def title(self, index, length, test_case):
            self.write(f'{colourise("{light_blue}")}')
            self.write("-" * 10)
            self.write(f"\nTest {index}/{length}: {test_case}\n")
            self.write("-" * 10)
            self.write(f'{colourise("{reset}")}\n')

        def success(
            self, case, total, type, expected_error, gramcheck_error, filename
        ):  # noqa: PLR0913
            self.write(filename + "\n")
            errorinfo = f", ({expected_error[4]})"
            x = colourise(
                (
                    "[{light_blue}{case:>%d}/{total}{reset}]"
                    + "[{green}PASS {type}{reset}] "
                    + "{error}:{correction} ({expectected_type}) {blue}=>{reset} "
                    + "{gramerr}:{errlist} ({gram_type})\n"
                )
                % len(str(total)),
                type=type,
                error=expected_error[0],
                correction=", ".join(expected_error[5]),
                expectected_type=f"{expected_error[4]}{errorinfo}",
                case=case,
                total=total,
                gramerr=gramcheck_error[0],
                errlist=f'[{", ".join(gramcheck_error[5])}]',
                gram_type=gramcheck_error[3],
            )
            self.write(x)

        def failure(
            self, case, total, type, expected_error, gramcheck_error, filename
        ):  # noqa: PLR0913
            self.write(filename + "\n")
            errorinfo = f", ({expected_error[4]})"
            x = colourise(
                (
                    "[{light_blue}{case:>%d}/{total}{reset}][{red}FAIL {type}"
                    "{reset}] {error}:{correction} ({expectected_type}) "
                    + "{blue}=>{reset} {gramerr}:{errlist} ({gram_type})\n"
                )
                % len(str(total)),
                type=type,
                error=expected_error[0],
                correction=", ".join(expected_error[5]),
                expectected_type=f"{expected_error[4]}{errorinfo}",
                case=case,
                total=total,
                gramerr=gramcheck_error[0],
                errlist=f'[{", ".join(gramcheck_error[5])}]',
                gram_type=gramcheck_error[3],
            )
            self.write(x)

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

    class CompactOutput(AllOutput):
        def result(self, number, count, test_case):
            passes = sum([count[key] for key in count if key.startswith("t")])
            fails = sum([count[key] for key in count if key.startswith("f")])
            out = f"{test_case} {passes}/{fails}/{passes + fails}"
            if fails:
                self.write(colourise("[{red}FAIL{reset}] {}\n", out))
            else:
                self.write(colourise("[{green}PASS{reset}] {}\n", out))

    class TerseOutput(AllOutput):
        def success(self, *args):
            self.write(colourise("{green}.{reset}"))

        def failure(self, *args):
            self.write(colourise("{red}!{reset}"))

        def result(self, *args):
            self.write("\n")

        def final_result(self, count):
            fails = sum([count[key] for key in count if key != "tp"])
            if fails:
                self.write(colourise("{red}FAIL{reset}\n"))
            else:
                self.write(colourise("{green}PASS{reset}\n"))

    class FinalOutput(AllOutput):
        def final_result(self, count):
            passes = sum([count[key] for key in count if key.startswith("t")])
            fails = sum([count[key] for key in count if key.startswith("f")])
            self.write(f"{passes}/{fails}/{passes+fails}")

    class NoOutput(AllOutput):
        def final_result(self, *args):
            pass

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

        out = self.config.get("out")
        out.title(item[0], length, item[1][0])

        expected_errors = item[1][1]["expected_errors"]
        gramcheck_errors = item[1][1]["gramcheck_errors"]
        filename = item[1][1]["filename"]

        for true_positive in self.has_true_positives(expected_errors, gramcheck_errors):
            count["tp"] += 1
            out.success(
                item[0], length, "tp", true_positive[0], true_positive[1], filename
            )

        for true_negative in self.has_true_negatives(expected_errors, gramcheck_errors):
            count["tn"] += 1
            out.success(
                item[0], length, "tn", true_negative[0], true_negative[1], filename
            )

        for false_positive_1 in self.has_false_positives_1(
            expected_errors, gramcheck_errors
        ):
            count["fp1"] += 1
            out.failure(
                item[0],
                length,
                "fp1",
                false_positive_1[0],
                false_positive_1[1],
                filename,
            )

        expected_error = ["", "", "", "", "", ""]
        for false_positive_2 in self.has_false_positives_2(
            expected_errors, gramcheck_errors
        ):
            count["fp2"] += 1
            out.failure(
                item[0], length, "fp2", expected_error, false_positive_2, filename
            )

        for false_negative_1 in self.has_false_negatives_1(
            expected_errors, gramcheck_errors
        ):
            count["fn1"] += 1
            out.failure(
                item[0],
                length,
                "fn1",
                false_negative_1[0],
                false_negative_1[1],
                filename,
            )

        for false_negative_2 in self.has_false_negatives_2(
            expected_errors, gramcheck_errors
        ):
            gramcheck_error = ["", "", "", "", "", []]
            count["fn2"] += 1
            out.failure(
                item[0], length, "fn2", false_negative_2, gramcheck_error, filename
            )

        out.result(item[0], count, item[1][0])

        for key in count:
            self.count[key] += count[key]

        # Did this test sentence as a whole pass or not
        return all(key.startswith("t") for key in count.keys())

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
            and any([correct in d_error[5] for correct in c_error[5]])
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
            and not any([correct in d_error[5] for correct in c_error[5]])
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

        return 1 if any(key.startswith("f") for key in self.count) else 0

    def __str__(self):
        return str(self.config.get("out"))

    @property
    def tests(self):
        return {test["uncorrected"]: test for test in self.paragraphs}
