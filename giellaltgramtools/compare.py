from giellaltgramtools.yaml_test_file import load_yaml_file
from giellaltgramtools.yaml_gramtest import has_dupes
from collections import Counter
from pathlib import Path

import click

YAML_PREFIX = """Config:
  Spec: ../pipespec.xml
  Variants: [smegram-dev]

Tests:
"""


@click.command()
@click.version_option()
@click.argument(
    "yaml_file_dir",
    type=click.Path(exists=True),
)
def main(yaml_file_dir: str):
    prefixes = {
        i.name.replace("-PASS.yaml", "").replace("-FAIL.yaml", "")
        for i in Path(yaml_file_dir).glob("*.yaml") if 'runtime' not in i.name
    }

    for prefix in prefixes:
        make_runtime_yaml(Path(yaml_file_dir), prefix)

def extract_tests_from_yaml(yaml_path: Path) -> list[str]:
    yaml_content = load_yaml_file(yaml_path)
    return yaml_content.tests


def show_dupes(tests: list[str]) -> None:
    counted_tests = Counter(tests)
    dupes = [test for test, count in counted_tests.items() if count > 1]
    for test in dupes:
        click.echo(f"    '{test}' appears {counted_tests[test]} times")
    click.echo("")

def make_runtime_yaml(yaml_dir_path: Path, prefix: str) -> None:
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
