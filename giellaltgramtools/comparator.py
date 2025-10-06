"""Compare output of divvun-checker with the output of divvun-runtime"""

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from giellaltgramtools.gramchecker import check_paragraphs_in_parallel
from giellaltgramtools.yaml_gramchecker import YamlGramChecker


@dataclass
class CheckerResult:
    form: str
    beg: int
    end: int
    err: str
    rep: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> "CheckerResult":
        """Create CheckerResult from dictionary, ignoring 'msg' field."""
        return cls(
            form=data["form"],
            beg=data["beg"],
            end=data["end"],
            err=data["err"],
            rep=data["rep"],
        )

    @classmethod
    def from_list(cls, data: list) -> "CheckerResult":
        """Create CheckerResult from list representation."""
        return cls(
            form=data[0],
            beg=data[1],
            end=data[2],
            err=data[3],
            rep=data[5],
        )

    def to_dict(self) -> dict:
        """Convert CheckerResult to dictionary for JSON serialization."""
        return {
            "form": self.form,
            "beg": self.beg,
            "end": self.end,
            "err": self.err,
            "rep": self.rep,
        }


def runtime_to_checker_results(json_data: list[dict]) -> list[CheckerResult]:
    """Convert JSON data to list of CheckerResult objects."""
    return [CheckerResult.from_dict(item) for item in json_data]


def checker_to_checker_results(errs: list[list]) -> list[CheckerResult]:
    """Convert list of lists to list of CheckerResult objects."""
    return [CheckerResult.from_list(item) for item in errs]


def parse_runtime_output(output: str) -> list[CheckerResult]:
    """Parse divvun-runtime output, stripping lines until first '[' and converting to CheckerResult objects."""
    lines = output.splitlines()

    # Find the first line that contains String("...")
    json_str = None
    for line in lines:
        if line.strip().startswith('String("') and line.strip().endswith('")'):
            # Extract JSON from String("...") format
            json_str = line.strip()[8:-2]  # Remove 'String("' and '")'
            break

    if json_str is None:
        return []

    try:
        json_data = json.loads(json_str)
        return runtime_to_checker_results(json_data)
    except json.JSONDecodeError:
        print("Error decoding JSON from divvun-runtime output")
        print(json_str)
        return []


def get_gramcheck_bundles(directory: Path) -> tuple[Path, Path]:
    zcheck_files = list(directory.parent.glob("*.zcheck"))
    if not zcheck_files:
        print("Warning: No .zcheck file found in parent directory", file=sys.stderr)
        sys.exit(1)
    zcheck = zcheck_files[0]

    drb_files = list(directory.parent.glob("*.drb"))
    if not drb_files:
        print("Warning: No .drb file found in parent directory", file=sys.stderr)
        sys.exit(1)
    drb = drb_files[0]
    return zcheck, drb


def get_paragraphs(zcheck: Path, yaml_file: Path) -> list[str]:
    gramchecker = YamlGramChecker(config={"spec": zcheck, "test_file": None})

    yaml_content = yaml.load(yaml_file.read_text(), Loader=yaml.FullLoader)
    paragraphs: list[str] = sorted(
        {
            gramchecker.paragraph_to_testdata(gramchecker.make_error_markup(text))[0]
            for text in yaml_content.get("Tests", [])
            if text.strip()
        }
    )

    return paragraphs


def get_divvun_runtime_results(
    drb: Path, paragraphs: list[str]
) -> list[list[CheckerResult]]:
    return [
        parse_runtime_output(
            subprocess.run(
                f"divvun-runtime run --path {drb}".split(),
                input=paragraph.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout.decode("utf-8")
        )
        for paragraph in paragraphs
    ]


def get_divvun_checker_results(
    zcheck: Path, paragraphs: list[str]
) -> list[list[CheckerResult]]:
    divvun_checker_lines = (
        check_paragraphs_in_parallel(
            command=f"divvun-checker --archive {zcheck}", paragraphs=paragraphs
        )
        .strip()
        .splitlines()
    )
    divvun_checker_results = sorted(
        json.loads(f"[{','.join(divvun_checker_lines)}]"),
        key=lambda x: x.get("text", ""),
    )
    return [
        checker_to_checker_results(result.get("errs", []))
        for result in divvun_checker_results
    ]


def is_known_issue(
    divvun_runtime_error: CheckerResult, divvun_checker_error: CheckerResult
) -> bool:
    if (
        divvun_runtime_error.err == "typo"
        and divvun_checker_error.err == "typo"
        and divvun_runtime_error.rep != divvun_checker_error.rep
    ):
        return True

    if (
        divvun_runtime_error.err != "typo"
        and divvun_checker_error.err != "typo"
        and divvun_runtime_error.rep != divvun_checker_error.rep
    ):
        return True

    if divvun_runtime_error.err == "typo" and divvun_checker_error.err != "typo":
        return True

    if divvun_runtime_error.err != "typo" and divvun_checker_error.err == "typo":
        return True

    return False


def make_report(
    paragraphs: list[str],
    divvun_checker_results: list[list[CheckerResult]],
    divvun_runtime_results: list[list[CheckerResult]],
):
    for paragraph, divvun_checker_result, divvun_runtime_result in zip(
        paragraphs, divvun_checker_results, divvun_runtime_results, strict=True
    ):
        if len(divvun_checker_result) != len(divvun_runtime_result):
            print(paragraph)
            print("Different number of errors found!")
            print("divvun-checker result:")
            print(
                json.dumps(
                    [asdict(err) for err in divvun_checker_result],
                    indent=2,
                    ensure_ascii=False,
                )
            )
            print("divvun-runtime result:")
            print(
                json.dumps(
                    [asdict(err) for err in divvun_runtime_result],
                    indent=2,
                    ensure_ascii=False,
                )
            )
            print("----")
        else:
            for divvun_runtime_error, divvun_checker_error in zip(
                divvun_runtime_result,
                divvun_checker_result,
                strict=True,
            ):
                if (
                    not is_known_issue(divvun_runtime_error, divvun_checker_error)
                    and divvun_runtime_error != divvun_checker_error
                ):
                    print(f"Mismatch for {paragraph} found!")
                    print("divvun-checker result:")
                    print(
                        json.dumps(
                            asdict(divvun_checker_error),
                            indent=2,
                            ensure_ascii=False,
                        )
                    )
                    print("divvun-runtime result:")
                    print(
                        json.dumps(
                            asdict(divvun_runtime_error),
                            indent=2,
                            ensure_ascii=False,
                        )
                    )
                    print("----")


def engine_comparator(directory_name: str):
    directory = Path(directory_name)
    zcheck, drb = get_gramcheck_bundles(directory)

    for yaml_file in directory.glob("*.yaml"):
        print(f"Comparing runtime and checker results for {yaml_file}...")
        paragraphs = get_paragraphs(zcheck, yaml_file)
        divvun_runtime_results = get_divvun_runtime_results(drb, paragraphs)
        divvun_checker_results = get_divvun_checker_results(zcheck, paragraphs)
        make_report(paragraphs, divvun_checker_results, divvun_runtime_results)
