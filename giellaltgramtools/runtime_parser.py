# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

"""Parser for divvun-runtime output."""
import json
import re
from dataclasses import dataclass

from giellaltgramtools.errordata import ErrorData
from giellaltgramtools.grammar_error_annotated_sentence import (
    GrammarErrorAnnotatedSentence,
)


@dataclass(frozen=True)
class DivvunRuntimeError:
    form: str
    start: int
    end: int
    error_id: str
    description: str
    suggestions: tuple[str, ...]


@dataclass
class DivvunRuntime:
    text: str
    errors: list[DivvunRuntimeError]
    encoding: str = "utf-8"


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI color codes from text.

    ANSI color codes follow the pattern:
    - ESC[<params>m where ESC is \x1b or \033
    - Can also have format like [48;2;R;G;Bm for 24-bit colors

    Args:
        text: String potentially containing ANSI escape codes

    Returns:
        Clean string without ANSI codes
    """
    # Pattern matches:
    # \x1b or \033 (ESC character)
    # \[ (opening bracket)
    # [0-9;]+ (parameters like 48;2;239;241;245)
    # [a-zA-Z] (final character like 'm', 'K', etc.)
    ansi_escape = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
    return ansi_escape.sub("", text)


def find_json_end(text: str, start_index: int) -> int:
    """Find the end index of a JSON object starting from start_index.

    This function counts opening and closing braces to find the matching
    closing brace for the JSON object.

    Args:
        text: The full text containing JSON
        start_index: The index where the JSON object starts (the '{' character)
    Returns:
        The index just after the closing '}' of the JSON object
    """
    brace_count = 0
    for i in range(start_index, len(text)):
        if text[i] == "{":
            brace_count += 1
        elif text[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                return i + 1  # Return index after the closing brace
    return -1  # Not found


def parse_runtime_response(output: str) -> DivvunRuntime:
    """Extract clean JSON from divvun-runtime output.

    divvun-runtime may output:
    - ANSI color codes for pretty printing
    - Log messages to stderr (should be filtered by subprocess)
    - The actual JSON response

    Args:
        output: Raw output from divvun-runtime

    Returns:
        DivvunRuntime: Parsed DivvunRuntime object
    """
    # First, strip ANSI color codes
    clean_output = strip_ansi_codes(output)

    # Find "text": which is guaranteed to be in the JSON object
    text_key = clean_output.find('"text":')
    if text_key == -1:
        return DivvunRuntime(text="", errors=[], encoding="utf-8")

    # Search backwards from "text": to find the opening brace of the JSON object
    json_start = clean_output.rfind("{", 0, text_key)
    if json_start == -1:
        return DivvunRuntime(text="", errors=[], encoding="utf-8")

    json_end = find_json_end(clean_output, json_start)

    if json_end == -1:
        return DivvunRuntime(text="", errors=[], encoding="utf-8")

    data = json.loads(clean_output[json_start:json_end])

    return DivvunRuntime(
        text=data.get("text", ""),
        errors=[
            DivvunRuntimeError(
                form=error["form"],
                start=error["start"],
                end=error["end"],
                error_id=error["error_id"],
                description=error["description"],
                suggestions=tuple(error.get("suggestions", [])),
            )
            for error in data.get("errors", [])
        ],
        encoding=data.get("encoding", "utf-8"),
    )


def runtime_to_char_offsets(runtime_response: DivvunRuntime) -> DivvunRuntime:
    """Convert all error offsets from byte to character offsets.

    Args:
        runtime_response: DivvunRuntime object with byte offsets
    Returns:
        DivvunRuntime object with character offsets
    """
    text = runtime_response.text

    return DivvunRuntime(
        text=runtime_response.text,
        errors=[
            DivvunRuntimeError(
                form=error.form,
                start=byte_offset_to_char_offset(text, error.start),
                end=byte_offset_to_char_offset(text, error.end),
                error_id=error.error_id,
                description=error.description,
                suggestions=error.suggestions,
            )
            for error in runtime_response.errors
        ],
        encoding=runtime_response.encoding,
    )


def errordata_from_runtime(
    errors: list[DivvunRuntimeError], sentence_start: int, sentence_end: int
) -> list[ErrorData]:
    """Find errors that belong to this sentence."""
    return [
        ErrorData(
            error_string=error.form,
            start=error.start - sentence_start,
            end=error.end - sentence_start,
            error_type=error.error_id,
            explanation=error.description,
            suggestions=error.suggestions,
        )
        for error in errors
        if sentence_start <= error.start < sentence_end
    ]


def runtime_to_grammar_error_annotated_sentences(
    orig_divvun_runtime: str,
) -> list[GrammarErrorAnnotatedSentence]:
    """Split a DivvunRuntime string with multiple sentences into separate objects.

    Args:
        input_str: JSON string representing DivvunRuntime data.

    Returns:
        List of GrammarErrorAnnotatedSentence, one per sentence.
    """
    runtime = runtime_to_char_offsets(parse_runtime_response(orig_divvun_runtime))
    text = runtime.text
    errors = runtime.errors

    # Split text by newlines (sentences)
    sentences = text.split("\n")

    # Track position in original text
    current_pos = 0

    new_data: list[GrammarErrorAnnotatedSentence] = []
    for sentence in sentences:
        sentence_end = current_pos + len(sentence)
        new_data.append(
            GrammarErrorAnnotatedSentence(
                sentence=sentence,
                errors=errordata_from_runtime(
                    errors, sentence_start=current_pos, sentence_end=sentence_end
                ),
            )
        )
        current_pos = sentence_end + 1

    return new_data


def byte_offset_to_char_offset(text: str, byte_offset: int) -> int:
    """Convert byte offset to character offset in UTF-8 text.

    Args:
        text: The text string
        byte_offset: Byte offset in UTF-8 encoding

    Returns:
        Character offset (position in the string)
    """
    # Encode to bytes and take the substring up to byte_offset
    byte_text = text.encode("utf-8")
    # Decode the substring to get character count
    char_text = byte_text[:byte_offset].decode("utf-8", errors="ignore")
    return len(char_text)
