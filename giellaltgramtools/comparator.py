"""Compare output of divvun-checker with the output of divvun-runtime"""
import os
import sys
from collections import Counter
from pathlib import Path

import click

from giellaltgramtools.yaml_gramchecker import GramCheckerSentenceError
from giellaltgramtools.yaml_gramtest import YamlGramTest, has_dupes
from giellaltgramtools.yaml_test_file import load_yaml_file

YAML_PREFIX = """Config:
  Spec: ../pipespec.xml
  Variants: [smegram-dev]

Tests:
"""

def engine_comparator(language: str):
    """Compare divvun-checker and divvun-runtime test results.

    Args:
        language: Language code to determine test file directory
    """
    directory = get_language_directory(language)

    remove_runtime_tests(directory)
    per_prefix_operations(directory)



def get_language_directory(language: str) -> Path:
    """Get the path to the grammarcheckers tests directory for the given language.

    Returns:
        Path: Path to the grammarcheckers tests directory for the given language.
    """
    gtlangs = os.getenv("GTLANGS")
    if gtlangs is None:
        print("Error: GTLANGS environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    assert gtlangs is not None  # for mypy
    return Path(gtlangs) / f"lang-{language}" / "tools/grammarcheckers/tests"


def remove_runtime_tests(directory: Path) -> None:
    """Remove existing runtime test files in the given directory.

    Args:
        directory: Path to the directory to remove runtime test files from.
    """
    for runtime_test_file in directory.glob("*-runtime-*.yaml"):
        runtime_test_file.unlink()


def per_prefix_operations(yaml_dir_path: Path) -> None:
    prefixes = {
        i.name.replace("-PASS.yaml", "").replace("-FAIL.yaml", "")
        for i in yaml_dir_path.glob("*.yaml")
        if "runtime" not in i.name
    }

    for prefix in sorted(prefixes):
        runtime_yaml_path_fail = make_runtime_yaml(yaml_dir_path, prefix)
        try:
            test_checker(yaml_dir_path, prefix)
            test_runtime(runtime_yaml_path_fail)
        except GramCheckerSentenceError as error:
            print(f"\n{error!r}\n", file=sys.stderr)


def test_checker(yaml_dir_path: Path, prefix: str) -> None:
    """Run divvun-checker tests on the given YAML file.

    Args:
        yaml_dir_path: Path to the directory containing the YAML file.
        prefix: Prefix of the YAML file to test.
    """
    for type_ in ["PASS", "FAIL"]:
        yaml_path = yaml_dir_path / f"{prefix}-{type_}.yaml"
        if yaml_path.exists():
            print(f"Running divvun-checker tests on {yaml_path} …")
            run_yaml_tests(yaml_path, use_runtime=False)


def test_runtime(yaml_path: Path) -> None:
    """Run divvun-runtime tests on the given YAML file.

    Args:
        yaml_path: Path to the YAML file to test.
    """
    print(f"Running divvun-runtime tests on {yaml_path}...", flush=True, end=" ")
    try:
        run_yaml_tests(yaml_path, use_runtime=True)
    except SystemExit as exc:  # keep the compare loop running across prefixes
        if exc.code not in (0, None):
            raise
    print("Done.", flush=True)


def build_yaml_ctx(use_runtime: bool) -> click.Context:
    """Create a minimal Click context compatible with YamlGramTest."""

    cmd = click.Command("compare-helper")
    ctx = click.Context(cmd)
    ctx.obj = {
        "colour": False,
        "hide_passes": False,
        "spec": None,
        "variant": None,
        "use_runtime": use_runtime,
        "output": "silent",
        "move_tests": True,
        "remove_dupes": False,
    }
    return ctx


def run_yaml_tests(yaml_path: Path, use_runtime: bool) -> int:
    """Run a YAML test file directly through YamlGramTest without sys.exit side-effects."""

    ctx = build_yaml_ctx(use_runtime)
    tester = YamlGramTest(ctx, yaml_path)
    ret = tester.run()
    sys.stdout.write(str(tester))
    return ret


def make_runtime_yaml(yaml_dir_path: Path, prefix: str) -> Path:
    pass_test_yaml = yaml_dir_path / f"{prefix}-PASS.yaml"
    if pass_test_yaml.exists():
        pass_tests = extract_tests_from_yaml(pass_test_yaml)
        if has_dupes(pass_tests):
            click.echo(f"  Found duplicates in {prefix}-PASS.yaml")
            show_dupes(pass_tests)
    else:
        pass_tests = []

    fail_test_yaml = yaml_dir_path / f"{prefix}-FAIL.yaml"
    if fail_test_yaml.exists():
        fail_tests = extract_tests_from_yaml(fail_test_yaml)
        if has_dupes(fail_tests):
            click.echo(f"  Found duplicates in {prefix}-FAIL.yaml")
            show_dupes(fail_tests)
    else:
        fail_tests = []

    all_tests = list(set(pass_tests) | set(fail_tests))
    if has_dupes(all_tests):
        click.echo(
            f"  Found duplicates across {prefix}-PASS.yaml and {prefix}-FAIL.yaml"
        )
        show_dupes(all_tests)

    runtime_yaml_path_fail = yaml_dir_path / f"{prefix}-runtime-FAIL.yaml"

    tests = "\n".join(f"  - {repr(test)}" for test in set(all_tests))
    runtime_yaml_content = f"{YAML_PREFIX}{tests}\n"
    runtime_yaml_path_fail.write_text(runtime_yaml_content)

    return runtime_yaml_path_fail


def show_dupes(tests: list[str]) -> None:
    counted_tests = Counter(tests)
    dupes = [test for test, count in counted_tests.items() if count > 1]
    for test in dupes:
        click.echo(f"    '{test}' appears {counted_tests[test]} times")
    click.echo("")


def extract_tests_from_yaml(yaml_path: Path) -> list[str]:
    yaml_content = load_yaml_file(yaml_path)
    return yaml_content.tests
