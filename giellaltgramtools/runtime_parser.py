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
