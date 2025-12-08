# -*- coding:utf-8 -*-

"""Tests for runtime_parser module."""

from giellaltgramtools.runtime_parser import (
    extract_json_from_runtime_output,
    parse_runtime_response,
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
    assert result["text"] == "Mun lea\\nDonn"
    assert len(result["errors"]) == 1
    assert result["errors"][0]["form"] == "lea"
