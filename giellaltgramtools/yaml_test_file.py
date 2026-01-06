import sys
from dataclasses import dataclass
from pathlib import Path

from yaml import FullLoader, load
from yaml.parser import ParserError
from yaml.scanner import ScannerError


@dataclass
class YamlTestFile:
    spec: Path
    variant: str
    tests: list[str]


def load_yaml_file(yaml_test_file: Path) -> YamlTestFile:
    try:
        yaml_content = load(yaml_test_file.read_text(), Loader=FullLoader)
    except (ScannerError, ParserError) as error:
        print(
            f"ERROR: Could not parse YAML file {yaml_test_file}:\n{error}",
            file=sys.stderr,
        )
        sys.exit(99)

    config = yaml_content.get("Config", {})
    if "Spec" not in config:
        print(
            f"ERROR: No spec in {yaml_test_file}",
            file=sys.stderr,
        )
        sys.exit(99)
    if "Variants" not in config or not config["Variants"]:
        print(
            f"ERROR: No variants in {yaml_test_file}",
            file=sys.stderr,
        )
        sys.exit(99)

    if not yaml_content.get("Tests", []):
        print(
            f"ERROR: No tests in {yaml_test_file}",
            file=sys.stderr,
        )
        sys.exit(99)

    return YamlTestFile(
        spec=yaml_test_file.parent / yaml_content.get("Config").get("Spec"),
        variant=yaml_content.get("Config").get("Variants")[0],
        tests=yaml_content["Tests"],
    )
