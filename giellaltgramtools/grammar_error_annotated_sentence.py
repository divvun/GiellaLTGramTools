from dataclasses import dataclass, field

from corpustools.error_annotated_sentence import ErrorAnnotatedSentence

from giellaltgramtools.errordata import ErrorData, error_markup_to_error_data


@dataclass
class GrammarErrorAnnotatedSentence:
    sentence: str
    errors: list[ErrorData] = field(default_factory=list)

def error_annotated_sentence_to_grammar_error_annotated_sentence(
    error_annotated_sentence: ErrorAnnotatedSentence
) -> GrammarErrorAnnotatedSentence:
    errors: list[ErrorData]   = []
    offset = len(error_annotated_sentence.head)

    for error_markup_segment in error_annotated_sentence.errors:
        error_data = error_markup_to_error_data(
            error_markup_segment.error_markup, offset
        )
        errors.append(error_data)
        offset += len(error_data.error_string + error_markup_segment.tail)
        
    return GrammarErrorAnnotatedSentence(
        sentence=error_annotated_sentence.uncorrected_text(),
        errors=errors
    )