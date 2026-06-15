import sys
from collections import namedtuple
from pathlib import Path

from giellaltgramtools.candidates import archive_path_to_variant
from giellaltgramtools.gramchecker import check_paragraphs_in_parallel

ASR_Result = namedtuple("ASR_Result", ["filename", "producer"])
ASR_grammarchecker_result = namedtuple(
    "ASR_grammarchecker_result", ["producer", "checker_result"]
)


def parse_asr_output(asr_file: Path) -> dict[str, list[ASR_Result]]:
    """Parse ASR output file and return a mapping of sentences to producers."""
    sentence_to_producers: dict[str, list[ASR_Result]] = {}

    for line in asr_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("FILE:"):
            current_file = line.strip()
        if "\t" in line:
            producer, sentence = line.split("\t")
            sentence_to_producers.setdefault(sentence, []).append(
                ASR_Result(filename=current_file, producer=producer)
            )

    return sentence_to_producers


def asr_output_checker(asr_file: Path, archive_path: Path) -> None:
    """Check ASR output against the grammar archive."""

    parsed_asr_output = parse_asr_output(asr_file)
    print(
        f"Parsed ASR output: {len(parsed_asr_output)} unique sentences found.\n",
        "This may take a while depending on the number of sentences.",
        file=sys.stderr,
    )
    variant = archive_path_to_variant(archive_path)
    checker_results = check_paragraphs_in_parallel(
        command=f"divvun-checker --archive {archive_path} --variant {variant}",
        paragraphs=list(parsed_asr_output.keys()),
    )
    asr_grammarchecker_results: dict[str, list[ASR_grammarchecker_result]] = {}
    for checker_result in checker_results:
        for asr_result in parsed_asr_output.get(checker_result.sentence, []):
            asr_grammarchecker_results.setdefault(asr_result.filename, []).append(
                ASR_grammarchecker_result(
                    producer=asr_result.producer, checker_result=checker_result
                )
            )

    asr_result_file = asr_file.with_suffix(".grammarcheck_results.txt")
    asr_result_file.write_text(
        "\n".join(print_asr_grammarchecker_results(asr_grammarchecker_results)),
        encoding="utf-8",
    )
    print(f"ASR grammar checker results written to: {asr_result_file}", file=sys.stderr)


def print_asr_grammarchecker_results(
    results: dict[str, list[ASR_grammarchecker_result]],
) -> list[str]:
    """Print ASR grammar checker results in a readable format."""
    resulting_lines: list[str] = []
    for filename, grammarchecker_results in results.items():
        resulting_lines.append(f"{filename}:")

        for result in grammarchecker_results:
            result_dict: dict[str, int] = {}
            for error in result.checker_result.errors:
                result_dict[error.error_type] = result_dict.get(error.error_type, 0) + 1
            error_counts = ", ".join(
                [f"{error_type}:{count}" for error_type, count in result_dict.items()]
            )
            resulting_lines.append(
                f"{result.producer}\t{result.checker_result.sentence}"
                f"\t{len(result.checker_result.errors)}"
                f"\t{error_counts}"
                f"\t{result.checker_result.to_manual_markup()}"
            )
        resulting_lines.append("")

    return resulting_lines
