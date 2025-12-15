# -*- coding:utf-8 -*-

"""Tests for runtime_parser module."""

from giellaltgramtools.runtime_parser import (
    convert_runtime_error_to_checker_format,
    convert_runtime_to_checker_format,
    extract_json_from_runtime_output,
    parse_runtime_response,
    split_runtime_output_by_lines,
    strip_ansi_codes,
)


def test_strip_ansi_codes():
    """Test ANSI code removal."""
    colored_text = "\x1b[48;2;239;241;245m\x1b[38;2;79;91;102mHello\x1b[0m"
    assert strip_ansi_codes(colored_text) == "Hello"


def test_extract_json_simple():
    """Test JSON extraction from simple colored output."""
    output = '\x1b[38;2;79;91;102m{"text": "test"}\x1b[0m'
    result = extract_json_from_runtime_output(output)
    assert result == '{"text": "test"}'


def test_parse_runtime_response():
    """Test full parsing of runtime response."""
    # Simplified version of your example
    output = '''\x1b[48;2;239;241;245m\x1b[38;2;79;91;102m{
  "text": "Mun lea\\nDonn",
  "errors": [
    {
      "form": "lea",
      "start": 4,
      "end": 7,
      "error_id": "err-syn-number_congruence-subj-verb"
    }
  ],
  "encoding": "utf-8"
}\x1b[0m'''
    
    result = parse_runtime_response(output)
    assert result["text"] == "Mun lea\nDonn"
    assert len(result["errors"]) == 1
    assert result["errors"][0]["form"] == "lea"


def test_split_runtime_output_by_lines():
    """Test splitting multi-line runtime output."""
    runtime_response = {
        "text": "Mun leam\nDonn",
        "errors": [
            {"form": "leam", "start": 4, "end": 8, "error_id": "err-typo"},
            {"form": "Donn", "start": 9, "end": 13, "error_id": "err-typo"}
        ]
    }
    
    results = split_runtime_output_by_lines(runtime_response)
    
    assert len(results) == 2
    assert results[0]["text"] == "Mun leam"
    assert len(results[0]["errors"]) == 1
    assert results[0]["errors"][0]["start"] == 4  # Adjusted to line start
    
    assert results[1]["text"] == "Donn"
    assert len(results[1]["errors"]) == 1
    assert results[1]["errors"][0]["start"] == 0  # Adjusted to line start


def test_convert_runtime_error_to_checker_format():
    """Test error format conversion."""
    runtime_error = {
        "form": "leam",
        "start": 4,
        "end": 8,
        "error_id": "err-typo",
        "title": "Spelling error",
        "description": "Not in the dictionary.",
        "suggestions": ["lean"]
    }
    
    checker_error = convert_runtime_error_to_checker_format(runtime_error)
    
    assert checker_error == [
        "leam",
        4,
        8,
        "typo",  # "err-" prefix removed
        "Not in the dictionary.",
        ["lean"],
        "Spelling error"
    ]


def test_convert_runtime_to_checker_format():
    """Test full conversion to checker format."""
    runtime_response = {
        "text": "Mun leam\nDonn",
        "errors": [
            {
                "form": "leam",
                "start": 4,
                "end": 8,
                "error_id": "err-typo",
                "title": "Spelling error",
                "description": "Not in dictionary",
                "suggestions": []
            }
        ]
    }
    
    checker_format = convert_runtime_to_checker_format(runtime_response)
    
    assert len(checker_format) == 2
    assert checker_format[0]["text"] == "Mun leam"
    assert len(checker_format[0]["errs"]) == 1
    assert checker_format[1]["text"] == "Donn"
    assert len(checker_format[1]["errs"]) == 0
