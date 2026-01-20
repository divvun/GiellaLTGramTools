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


class YamlTestFileError(Exception):
    """Custom exception for YAML test file errors."""

    pass


def load_yaml_file(yaml_test_file: Path) -> YamlTestFile:
    """Load a YAML test file and return its contents as a YamlTestFile dataclass.

    Args:
        yaml_test_file (Path): The path to the YAML test file.
    Returns:
        YamlTestFile: A dataclass containing the spec path, variant, and tests.
    Raises:
        YamlTestFileError: If there are issues with the YAML file structure.
    """
    try:
        yaml_content = load(yaml_test_file.read_text(), Loader=FullLoader)
    except (ScannerError, ParserError) as error:
        raise YamlTestFileError(
            f"ERROR: yaml syntax error in {yaml_test_file}:\n{error}",
        ) from error

    config = yaml_content.get("Config", {})
    if "Spec" not in config:
        raise YamlTestFileError(
            f"ERROR: No spec in {yaml_test_file}",
        )
    if "Variants" not in config or not config["Variants"]:
        raise YamlTestFileError(
            f"ERROR: No variants in {yaml_test_file}",
        )

    if not yaml_content.get("Tests", []):
        raise YamlTestFileError(
            f"ERROR: No tests in {yaml_test_file}",
        )

    return YamlTestFile(
        spec=yaml_test_file.parent / yaml_content.get("Config").get("Spec"),
        variant=yaml_content.get("Config").get("Variants")[0],
        tests=yaml_content["Tests"],
    )
