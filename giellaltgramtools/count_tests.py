from pathlib import Path

from giellaltgramtools.yaml_test_file import load_yaml_file


def count_test_cases(test_directory: str, filter_string: str) -> int:
    return sum(
        len(load_yaml_file(yaml_file).tests)
        for yaml_file in Path(test_directory).glob(f"*{filter_string}.yaml")
    )

def report_test_counts(test_directory: str) -> None:
    pass_count = count_test_cases(test_directory, "PASS")
    fail_count = count_test_cases(test_directory, "FAIL")
    print(f"Total PASS tests: {pass_count}")
    print(f"Total FAIL tests: {fail_count}")
