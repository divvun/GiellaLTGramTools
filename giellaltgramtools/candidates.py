from pathlib import Path
from typing import Any

import yaml

from giellaltgramtools.gramchecker import check_paragraphs_in_parallel


def archive_path_to_variant(archive_path: Path) -> str:
    """Convert archive path to language code.

    Args:
        archive_path: Path to the grammar checker archive.
    Returns:
        tuple[str, str]: The language code and archives variant name.
    """
    langs = {
        "se": "sme",
        "ga": "gle",
        "fo": "fao",
        "kl": "kal",
    }
    archive_lang = archive_path.stem
    return f"{langs.get(archive_lang, archive_lang)}gram"


def gramcheck_candidates(
    input_file: str, archive_path: Path, filter_text: str | None
) -> dict[str, Any]:
    """Run grammar checker on candidate file and return results."""
    variant = archive_path_to_variant(archive_path)
    checker_results = check_paragraphs_in_parallel(
        command=f"divvun-checker --archive {archive_path} --variant {variant}",
        paragraphs=Path(input_file).read_text().splitlines(),
    )

    return {
        "Config": {"Spec": "../../pipespec.xml", "Variants": [variant]},
        "Tests": [result.to_manual_markup() for result in checker_results]
        if filter_text is None
        else [
            result.to_manual_markup()
            for result in checker_results
            if any(filter_text == error.error_type for error in result.errors)
        ],
    }


def create_yaml_candidates(
    input_file: str, candidate_name: str, archive_path: Path, filter_text: str | None
) -> None:
    """Create candidate files for testing.
    
    Args:
        input_file: Path to the input file containing test sentences.
        candidate_name: Name of the candidate file to be created (without extension).
        archive_path: Path to the grammar checker archive.
        filter_text: If provided, only include candidates of this error type 
            (e.g. 'msyn').
    """
    checker_results = gramcheck_candidates(
        input_file=input_file,
        archive_path=archive_path,
        filter_text=filter_text,
    )

    yaml_content = yaml.dump(checker_results, allow_unicode=True, indent=2, width=2000)
    candidate_file_path = (
        archive_path.parent / "tests/candidates" / f"{candidate_name}.yaml"
    )
    candidate_file_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_file_path.write_text(yaml_content)
    print(f"Candidate file created at: {candidate_file_path}")
