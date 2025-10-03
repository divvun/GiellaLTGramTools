"""Compare output of divvun-checker with the output of divvun-runtime"""

import json
import subprocess
import sys
from pathlib import Path

import yaml

from giellaltgramtools.gramchecker import check_paragraphs_in_parallel
from giellaltgramtools.yaml_gramchecker import YamlGramChecker


def engine_comparator(directory_name: str):
    directory = Path(directory_name)
    zcheck_files = list(directory.parent.glob("*.zcheck"))
    if not zcheck_files:
        print("Warning: No .zcheck file found in parent directory", file=sys.stderr)
        sys.exit(1)
    zcheck = zcheck_files[0]

    gramchecker = YamlGramChecker(config={"spec": zcheck, "test_file": None})
    drb_files = list(directory.parent.glob("*.drb"))
    if not drb_files:
        print("Warning: No .drb file found in parent directory", file=sys.stderr)
        sys.exit(1)
    drb = drb_files[0]

    for i, yaml_file in enumerate(directory.glob("*.yaml")):
        if i < 1:
            yaml_content = yaml.load(yaml_file.read_text(), Loader=yaml.FullLoader)
            paragraphs: list[str] = sorted(
                {
                    gramchecker.paragraph_to_testdata(
                        gramchecker.make_error_markup(text)
                    )[0]
                    for text in yaml_content.get("Tests", [])
                    if text.strip()
                }
            )
            divvun_runtime_results = [
                json.loads(
                    "\n".join(
                        subprocess.run(
                            f"divvun-runtime run --path {drb}".split(),
                            input=paragraph.encode("utf-8"),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True,
                        )
                        .stdout.decode("utf-8")
                        .splitlines()[1:]
                    )
                )
                for paragraph in paragraphs
            ]
            divvun_checker_lines = (
                check_paragraphs_in_parallel(
                    command=f"divvun-checker --archive {zcheck}", paragraphs=paragraphs
                )
                .strip()
                .splitlines()
            )
            divvun_checker_results = json.loads(f"[{','.join(divvun_checker_lines)}]")
            divvun_checker_results = sorted(
                divvun_checker_results, key=lambda x: x.get("text", "")
            )

            for divvun_checker_result, divvun_runtime_result in zip(
                divvun_checker_results, divvun_runtime_results, strict=True
            ):
                errs = divvun_checker_result.get("errs", [])
                checker_dicts = [
                    {
                        "form": err[0],
                        "beg": err[1],
                        "end": err[2],
                        "err": err[3],
                        "rep": err[5],
                    }
                    for err in errs
                ]
                if errs and divvun_runtime_result:
                    # print("Checker dicts:", checker_dicts)
                    # print("Runtime dicts:", divvun_runtime_result)
                    if len(checker_dicts) != len(divvun_runtime_result) or not all(
                        has_same_attributes(d, r)
                        for d, r in zip(
                            checker_dicts, divvun_runtime_result, strict=True
                        )
                    ):
                        print("Mismatch found!")
                        print("divvun-checker result:")
                        print(
                            json.dumps(
                                divvun_checker_result, indent=2, ensure_ascii=False
                            )
                        )
                        print("divvun-runtime result:")
                        print(
                            json.dumps(
                                divvun_runtime_result, indent=2, ensure_ascii=False
                            )
                        )
                        print("----")
            print(f"Checked {len(paragraphs)} paragraphs in {yaml_file.name}")


def has_same_attributes(checker_result: dict, runtime_result: dict) -> bool:
    mostly_equal: bool = (
        checker_result.get("form") == runtime_result.get("form")
        and checker_result.get("beg") == runtime_result.get("beg")
        and checker_result.get("end") == runtime_result.get("end")
        and checker_result.get("err") == runtime_result.get("err")
    )

    if runtime_result.get("err") != "typo":
        return mostly_equal and checker_result.get("rep", []) == runtime_result.get(
            "rep", []
        )
    return mostly_equal
