import re
from collections import defaultdict
from pathlib import Path
from subprocess import PIPE, run

import yaml
from corpustools.sentencedivider import make_sentences

from giellaltgramtools.gramchecker import check_paragraphs_in_parallel
from giellaltgramtools.grammar_error_annotated_sentence import (
    GrammarErrorAnnotatedSentence,
)


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


def make_tokenised_output(input_bytes: bytes, lang_directory: Path) -> str:
    tokeniser = lang_directory / "tools/tokenisers/tokeniser-gramcheck-gt-desc.pmhfst"
    if not tokeniser.is_file():
        raise FileNotFoundError(f"Tokeniser not found at: {tokeniser}")
    command = ["hfst-tokenise", "--print-all", str(tokeniser)]
    result = run(
        command,
        input=input_bytes,
        stdout=PIPE,
        stderr=PIPE,
        check=True,
    )
    return result.stdout.decode("utf-8")


def classify_checker_result(result: GrammarErrorAnnotatedSentence) -> set[str]:
    """Classify the grammar checker result into error types.

    Args:
        result: A GrammarErrorAnnotatedSentence object containing the checker result.
    Returns:
        set[str]: A set of error types identified in the result.
    """
    if not result.errors or all(error.error_type == "typo" for error in result.errors):
        return {"generic"}

    return {error.error_type for error in result.errors if error.error_type != "typo"}


def gramcheck_candidates(
    input_bytes: bytes, archive_path: Path
) -> list[tuple[str, GrammarErrorAnnotatedSentence]]:
    """Run grammar checker on candidate file and return results."""
    sentences = make_sentences(
        make_tokenised_output(input_bytes, archive_path.parent.parent.parent)
    )

    variant = archive_path_to_variant(archive_path)
    checker_results = check_paragraphs_in_parallel(
        command=f"divvun-checker --archive {archive_path} --variant {variant}",
        paragraphs=[
            sentence
            for sentence in sentences
            if not sentence.strip() or "......" not in sentence
        ],
    )

    return [
        (error_type, result)
        for result in checker_results
        for error_type in classify_checker_result(result)
    ]


def error_type_to_file_component(error_type: str) -> str:
    """Convert error type to a filename-safe component."""
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", error_type).strip("-")
    return safe_name or "unknown"


def create_yaml_candidates(
    input_bytes: bytes, candidate_prefix: str, archive_path: Path
) -> None:
    """Create candidate files for testing.

    Args:
        input_bytes: Input text as bytes.
        candidate_prefix: Prefix for the candidates file to be created.
        archive_path: Path to the grammar checker archive.
    """
    candidate_list = gramcheck_candidates(
        input_bytes=input_bytes,
        archive_path=archive_path,
    )

    candidates_by_type: dict[str, list[str]] = defaultdict(list)
    for error_type, result in candidate_list:
        candidates_by_type[error_type].append(result.to_manual_markup())

    if not candidates_by_type:
        print("No candidates found.")
        return

    candidate_directory = archive_path.parent / "tests" / "candidates"
    candidate_directory.mkdir(parents=True, exist_ok=True)

    variant = archive_path_to_variant(archive_path)
    spec_path = "../../pipespec.xml"

    for error_type, tests in sorted(candidates_by_type.items()):
        file_component = error_type_to_file_component(error_type)
        file_name = (
            f"{candidate_prefix}-{file_component}-FAIL.yaml"
            if candidate_prefix
            else f"{file_component}-FAIL.yaml"
        )
        candidate_file_path = candidate_directory / file_name

        yaml_content = yaml.safe_dump(
            {
                "Config": {
                    "Spec": spec_path,
                    "Variants": [variant],
                },
                "Tests": tests,
            },
            allow_unicode=True,
            indent=2,
            width=2000,
            sort_keys=False,
        )

        candidate_file_path.write_text(yaml_content)
        print(f"Candidate file created at: {candidate_file_path}")
