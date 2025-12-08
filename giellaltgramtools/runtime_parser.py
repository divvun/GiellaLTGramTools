# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

"""Parser for divvun-runtime output."""

import json
import re
from typing import Any


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
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    return ansi_escape.sub('', text)


def extract_json_from_runtime_output(output: str) -> str:
    """Extract clean JSON from divvun-runtime output.
    
    divvun-runtime may output:
    - ANSI color codes for pretty printing
    - Log messages to stderr (should be filtered by subprocess)
    - The actual JSON response
    
    Args:
        output: Raw output from divvun-runtime
        
    Returns:
        Clean JSON string
    """
    # First, strip ANSI color codes
    clean_output = strip_ansi_codes(output)
    
    # Find the JSON object boundaries
    json_start = clean_output.find('{')
    if json_start == -1:
        return "{}"
    
    # Count braces to find the complete JSON object
    brace_count = 0
    json_end = -1
    for i in range(json_start, len(clean_output)):
        if clean_output[i] == '{':
            brace_count += 1
        elif clean_output[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break
    
    if json_end == -1:
        return "{}"
    
    return clean_output[json_start:json_end]


def parse_runtime_response(output: str) -> dict[str, Any]:
    """Parse divvun-runtime JSON response.
    
    Args:
        output: Raw output from divvun-runtime command
        
    Returns:
        Parsed JSON as dictionary with keys: text, errors, encoding
        Returns empty dict on parse error
    """
    json_str = extract_json_from_runtime_output(output)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"text": "", "errors": [], "encoding": "utf-8"}


def split_runtime_output_by_lines(runtime_response: dict[str, Any]) -> list[dict[str, Any]]:
    """Split divvun-runtime output into separate results for each line.
    
    divvun-runtime treats entire input as one text block, but divvun-checker
    processes each line separately. This function splits the runtime output
    to match checker behavior.
    
    Args:
        runtime_response: Parsed JSON from divvun-runtime with keys:
            - text: Full input text (may contain \n)
            - errors: List of error objects
            - encoding: Text encoding
    
    Returns:
        List of dictionaries, one per line, each with:
            - text: Single line of text
            - errors: Errors for that line only (with adjusted positions)
    """
    text = runtime_response.get("text", "")
    all_errors = runtime_response.get("errors", [])
    
    # Split text by newlines
    lines = text.split("\n")
    results = []
    
    # Calculate line boundaries
    line_start = 0
    for line_text in lines:
        line_end = line_start + len(line_text)
        
        # Find errors that fall within this line
        line_errors = []
        for error in all_errors:
            error_start = error.get("start", 0)
            error_end = error.get("end", 0)
            
            # Check if error is within this line's boundaries
            if line_start <= error_start < line_end and error_end <= line_end:
                # Adjust error positions relative to line start
                adjusted_error = error.copy()
                adjusted_error["start"] = error_start - line_start
                adjusted_error["end"] = error_end - line_start
                line_errors.append(adjusted_error)
        
        results.append({
            "text": line_text,
            "errors": line_errors
        })
        
        # Move to next line (add 1 for the \n character)
        line_start = line_end + 1
    
    return results


def convert_runtime_error_to_checker_format(error: dict[str, Any]) -> list[Any]:
    """Convert a divvun-runtime error object to divvun-checker format.
    
    Runtime format:
    {
      "form": "leam",
      "start": 4,
      "end": 8,
      "error_id": "err-typo",
      "title": "Spelling error",
      "description": "Not in the dictionary.",
      "suggestions": []
    }
    
    Checker format (list):
    ["leam", 4, 8, "typo", "Ii leat sátnelisttus", [], "Čállinmeattáhus"]
    [form, start, end, error_type, description, suggestions, title]
    
    Args:
        error: Error dict from divvun-runtime
        
    Returns:
        List in divvun-checker format
    """
    # Remove "err-" prefix from error_id to get error type
    error_id = error.get("error_id", "")
    error_type = error_id.replace("err-", "") if error_id.startswith("err-") else error_id
    
    return [
        error.get("form", ""),
        error.get("start", 0),
        error.get("end", 0),
        error_type,
        error.get("description", ""),
        error.get("suggestions", []),
        error.get("title", "")
    ]


def convert_runtime_to_checker_format(runtime_response: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert divvun-runtime response to divvun-checker format.
    
    Converts from runtime's single-response format to checker's
    line-by-line format.
    
    Args:
        runtime_response: Parsed JSON from divvun-runtime
        
    Returns:
        List of dicts in divvun-checker format, one per line:
        {"text": "line text", "errs": [[form, start, end, type, desc, suggs, title], ...]}
    """
    line_results = split_runtime_output_by_lines(runtime_response)
    
    checker_format = []
    for line_result in line_results:
        checker_errors = [
            convert_runtime_error_to_checker_format(err)
            for err in line_result["errors"]
        ]
        
        checker_format.append({
            "text": line_result["text"],
            "errs": checker_errors
        })
    
    return checker_format


def runtime_output_to_checker_json_lines(output: str) -> str:
    """Convert raw divvun-runtime output to divvun-checker JSON lines format.
    
    This is the main conversion function that takes raw runtime output
    and returns newline-separated JSON objects matching checker format.
    
    Args:
        output: Raw output from divvun-runtime command (may include ANSI codes)
        
    Returns:
        String with one JSON object per line, matching divvun-checker format
    """
    # Parse runtime output
    runtime_response = parse_runtime_response(output)
    
    # Convert to checker format
    checker_results = convert_runtime_to_checker_format(runtime_response)
    
    # Convert to JSON lines (one JSON object per line)
    json_lines = [json.dumps(result, ensure_ascii=False) for result in checker_results]
    
    return "\n".join(json_lines)
