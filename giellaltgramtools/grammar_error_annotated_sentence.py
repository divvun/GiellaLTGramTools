import json
from dataclasses import dataclass, field

from corpustools.error_annotated_sentence import ErrorAnnotatedSentence

from giellaltgramtools.divvun_checker_fixes import fix_aistton, sort_by_range
from giellaltgramtools.errordata import (
    ErrorData,
    divvun_checker_to_error_data,
    error_markup_to_error_data,
)


@dataclass
class GrammarErrorAnnotatedSentence:
    sentence: str
    errors: list[ErrorData] = field(default_factory=list)


def error_annotated_sentence_to_grammar_error_annotated_sentence(
    error_annotated_sentence: ErrorAnnotatedSentence,
) -> GrammarErrorAnnotatedSentence:
    errors: list[ErrorData] = []
    offset = len(error_annotated_sentence.head)

    for error_markup_segment in error_annotated_sentence.errors:
        error_data = error_markup_to_error_data(
            error_markup_segment.error_markup, offset
        )
        errors.append(error_data)
        offset += len(error_data.error_string + error_markup_segment.tail)

    return GrammarErrorAnnotatedSentence(
        sentence=error_annotated_sentence.uncorrected_text(), errors=errors
    )


def divvun_checker_output_to_grammar_error_annotated_sentence(
    divvun_checker_output: str,
) -> GrammarErrorAnnotatedSentence:
    gram_error = json.loads(divvun_checker_output)
    return GrammarErrorAnnotatedSentence(
        sentence=gram_error.get("text"),
            errors=sort_by_range(fix_aistton(
                [
                    divvun_checker_to_error_data(d_error)
                    for d_error in gram_error.get("errs")
                ]
            )),
    )

def fix_paragraphs(
    result_str: str,
) -> list[GrammarErrorAnnotatedSentence]:
    """Convert divvun-checker output to a list of GrammarErrorAnnotatedSentence.

    Args:
        result_str: divvun-checker output as a string.
            Each line is a JSON object containing the grammar checker's
            result of an input string.
    Returns:
        List of GrammarErrorAnnotatedSentence.
    """
    return [
        divvun_checker_output_to_grammar_error_annotated_sentence(gram_error)
        for gram_error in result_str.strip().split("\n")
    ]


