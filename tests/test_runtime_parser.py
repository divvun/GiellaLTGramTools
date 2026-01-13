# -*- coding:utf-8 -*-

"""Tests for runtime_parser module."""

import json

from giellaltgramtools.grammar_error_annotated_sentence import (
    GrammarErrorAnnotatedSentence,
)
from giellaltgramtools.runtime_parser import (
    DivvunRuntime,
    DivvunRuntimeError,
    byte_offset_to_char_offset,
    errordata_from_runtime,
    find_json_end,
    parse_runtime_response,
    runtime_to_char_offsets,
    runtime_to_grammar_error_annotated_sentences,
    strip_ansi_codes,
)


def test_strip_ansi_codes():
    """Test ANSI code removal."""
    colored_text = "\x1b[48;2;239;241;245m\x1b[38;2;79;91;102mHello\x1b[0m"
    assert strip_ansi_codes(colored_text) == "Hello"


def test_strip_ansi_codes_multiple():
    """Test ANSI code removal with multiple codes."""
    colored_text = "\x1b[38;2;79;91;102mHello\x1b[0m\x1b[1mWorld\x1b[0m"
    assert strip_ansi_codes(colored_text) == "HelloWorld"


def test_find_json_end_simple():
    """Test finding JSON object boundaries."""
    text = '{"key": "value"} extra text'
    start = text.find("{")
    end = find_json_end(text, start)
    assert text[start:end] == '{"key": "value"}'


def test_find_json_end_nested():
    """Test finding JSON object with nested objects."""
    text = '{"key": {"nested": "value"}} extra'
    start = text.find("{")
    end = find_json_end(text, start)
    assert text[start:end] == '{"key": {"nested": "value"}}'


def test_find_json_end_not_found():
    """Test when JSON is not properly closed."""
    text = '{"key": "value"'
    start = text.find("{")
    end = find_json_end(text, start)
    assert end == -1


def test_parse_runtime_response_simple():
    """Test parsing simple runtime response."""
    output = '{"text": "Mun lean", "errors": [], "encoding": "utf-8"}'
    result = parse_runtime_response(output)
    assert isinstance(result, DivvunRuntime)
    assert result.text == "Mun lean"
    assert len(result.errors) == 0


def test_parse_runtime_response_with_errors():
    """Test parsing runtime response with errors."""
    output = """{
  "text": "Mun lea",
  "errors": [
    {
      "form": "lea",
      "start": 4,
      "end": 7,
      "error_id": "syn-number_congruence-subj-verb",
      "description": "Congruence error",
      "suggestions": ["lean"]
    }
  ],
  "encoding": "utf-8"
}"""
    result = parse_runtime_response(output)
    assert result.text == "Mun lea"
    assert len(result.errors) == 1
    # Access DivvunRuntimeError attributes using dot notation
    assert result.errors[0].form == "lea"
    assert result.errors[0].error_id == "syn-number_congruence-subj-verb"
    assert result.errors[0].suggestions == ("lean",)


def test_parse_runtime_response_with_ansi_codes():
    """Test parsing runtime response with ANSI color codes."""
    output = '\x1b[48;2;239;241;245m{"text": "test", "errors": [], "encoding": "utf-8"}\x1b[0m'
    result = parse_runtime_response(output)
    assert result.text == "test"
    assert len(result.errors) == 0


def test_parse_runtime_response_invalid():
    """Test parsing invalid output."""
    output = "No JSON here"
    result = parse_runtime_response(output)
    assert result.text == ""
    assert len(result.errors) == 0


def test_byte_offset_to_char_offset_ascii():
    """Test byte to char offset conversion with ASCII text."""
    text = "Hello World"
    assert byte_offset_to_char_offset(text, 0) == 0
    assert byte_offset_to_char_offset(text, 5) == 5
    assert byte_offset_to_char_offset(text, 11) == 11


def test_byte_offset_to_char_offset_utf8():
    """Test byte to char offset conversion with UTF-8 text."""
    # "é" takes 2 bytes in UTF-8
    text = "Café"  # 4 characters, 5 bytes
    assert byte_offset_to_char_offset(text, 0) == 0
    assert byte_offset_to_char_offset(text, 3) == 3  # "Caf"
    assert byte_offset_to_char_offset(text, 5) == 4  # "Café"


def test_byte_offset_to_char_offset_sami():
    """Test byte to char offset conversion with Sámi text."""
    # "á" takes 2 bytes in UTF-8
    text = "Mun"  # 3 characters, 3 bytes
    assert byte_offset_to_char_offset(text, 0) == 0
    assert byte_offset_to_char_offset(text, 3) == 3


def test_runtime_to_char_offsets():
    """Test converting runtime errors from byte to char offsets."""
    # Create runtime response with byte offsets
    runtime = DivvunRuntime(
        text="Mun lea",
        errors=[
            DivvunRuntimeError(
                form="lea",
                start=4,
                end=7,
                error_id="syn-number_congruence-subj-verb",
                description="Congruence error",
                suggestions=("lean",),
            )
        ],
        encoding="utf-8",
    )

    result = runtime_to_char_offsets(runtime)
    assert result.text == "Mun lea"
    assert len(result.errors) == 1
    assert result.errors[0].start == 4
    assert result.errors[0].end == 7


def test_errordata_from_runtime_single_sentence():
    """Test converting runtime errors to ErrorData for single sentence."""
    errors = [
        DivvunRuntimeError(
            form="lea",
            start=4,
            end=7,
            error_id="syn-number_congruence-subj-verb",
            description="Congruence error",
            suggestions=("lean",),
        )
    ]

    result = errordata_from_runtime(errors, sentence_start=0, sentence_end=7)

    assert len(result) == 1
    assert result[0].error_string == "lea"
    assert result[0].start == 4
    assert result[0].end == 7
    assert result[0].error_type == "syn-number_congruence-subj-verb"
    assert result[0].explanation == "Congruence error"
    assert result[0].suggestions == ("lean",)


def test_errordata_from_runtime_multiple_sentences():
    """Test converting runtime errors to ErrorData for multiple sentences."""
    errors = [
        DivvunRuntimeError(
            form="lea",
            start=4,
            end=7,
            error_id="syn-number_congruence-subj-verb",
            description="Congruence error",
            suggestions=("lean",),
        ),
        DivvunRuntimeError(
            form="badjel",
            start=20,
            end=26,
            error_id="typo",
            description="Not in dictionary",
            suggestions=("bajel", "badel"),
        ),
    ]

    # First sentence: "Mun lea" (0-7)
    result1 = errordata_from_runtime(errors, sentence_start=0, sentence_end=7)
    assert len(result1) == 1
    assert result1[0].error_string == "lea"

    # Second sentence: "Mun badjel" (8-18) - note: no error in this range
    result2 = errordata_from_runtime(errors, sentence_start=8, sentence_end=18)
    assert len(result2) == 0

    # Third sentence with error: (14-26)
    result3 = errordata_from_runtime(errors, sentence_start=14, sentence_end=26)
    assert len(result3) == 1
    assert result3[0].error_string == "badjel"
    assert result3[0].start == 20 - 14  # Adjusted to sentence start


def test_errordata_from_runtime_adjusted_positions():
    """Test that error positions are adjusted relative to sentence start."""
    errors = [
        DivvunRuntimeError(
            form="word",
            start=10,
            end=14,
            error_id="typo",
            description="Error",
            suggestions=("wurd",),
        )
    ]

    result = errordata_from_runtime(errors, sentence_start=5, sentence_end=20)

    assert len(result) == 1
    assert result[0].start == 10 - 5  # 5
    assert result[0].end == 14 - 5  # 9


def test_split_json_by_sentences_single():
    """Test splitting single sentence."""
    runtime_dict = {
        "text": "Mun lean.",
        "errors": [
            {
                "form": "lean",
                "start": 4,
                "end": 8,
                "error_id": "typo",
                "description": "Typo",
                "suggestions": ["lean"],
            }
        ],
        "encoding": "utf-8",
    }
    json_output = json.dumps(runtime_dict)

    result = runtime_to_grammar_error_annotated_sentences(json_output)

    assert len(result) == 1
    assert isinstance(result[0], GrammarErrorAnnotatedSentence)
    assert result[0].sentence == "Mun lean."
    assert len(result[0].errors) == 1


def test_split_json_by_sentences_multiple():
    """Test splitting multiple sentences."""
    runtime_dict = {
        "text": "Mun lean.\nDonn",
        "errors": [
            {
                "form": "lean",
                "start": 4,
                "end": 8,
                "error_id": "typo",
                "description": "Typo",
                "suggestions": ["lean"],
            },
            {
                "form": "Donn",
                "start": 10,
                "end": 14,
                "error_id": "typo",
                "description": "Typo",
                "suggestions": ["Don"],
            },
        ],
        "encoding": "utf-8",
    }
    json_output = json.dumps(runtime_dict)

    result = runtime_to_grammar_error_annotated_sentences(json_output)

    assert len(result) == 2
    assert result[0].sentence == "Mun lean."
    assert len(result[0].errors) == 1
    assert result[0].errors[0].error_string == "lean"

    assert result[1].sentence == "Donn"
    assert len(result[1].errors) == 1
    assert result[1].errors[0].error_string == "Donn"
    # Position should be adjusted relative to sentence start
    assert result[1].errors[0].start == 10 - 10


def test_split_json_by_sentences_no_errors():
    """Test splitting sentences with no errors."""
    runtime_dict = {
        "text": "Correct sentence.\nAnother one.",
        "errors": [],
        "encoding": "utf-8",
    }
    json_output = json.dumps(runtime_dict)

    result = runtime_to_grammar_error_annotated_sentences(json_output)

    assert len(result) == 2
    assert result[0].sentence == "Correct sentence."
    assert len(result[0].errors) == 0
    assert result[1].sentence == "Another one."
    assert len(result[1].errors) == 0
