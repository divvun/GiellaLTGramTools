"""Compare output of divvun-checker with the output of divvun-runtime"""

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

from giellaltgramtools.gramchecker import check_paragraphs_in_parallel
from giellaltgramtools.yaml_gramchecker import YamlGramChecker


@dataclass
class CheckerResult:
    form: str
    beg: int
    end: int
    err: str
    rep: list[str]

    @classmethod
    def from_list(cls, data: list) -> "CheckerResult":
        """Create CheckerResult from list representation."""
        return cls(
            form=data[0],
            beg=data[1],
            end=data[2],
            err=data[3],
            rep=data[5],
        )
    
    def __eq__(self, other):
        """Compare CheckerResults using the lower cased err attributes.
        """
        if not isinstance(other, CheckerResult):
            return NotImplemented
        
        return (
            self.form == other.form and
            self.beg == other.beg and
            self.end == other.end and
            self.err.lower() == other.err.lower() and
            self.rep == other.rep
        )
    
    def __hash__(self):
        """Define hash to match the custom equality."""
        return hash((self.form, self.beg, self.end, tuple(self.rep)))


def parse_checker_output(output: str) -> list[list[CheckerResult]]:
    """Parse divvun-checker format output (newline-separated JSON objects)."""
    lines = output.strip().splitlines()
    if not lines:
        return []
    
    results = json.loads(f"[{','.join(lines)}]")
    return [
        [CheckerResult.from_list(err) for err in result.get("errs", [])]
        for result in results
    ]


def get_gramcheck_bundles(directory: Path) -> tuple[Path, Path]:
    """Find .zcheck and .drb files in parent directory."""
    zcheck_files = list(directory.parent.glob("*.zcheck"))
    if not zcheck_files:
        print("Warning: No .zcheck file found in parent directory", file=sys.stderr)
        sys.exit(1)
    zcheck = zcheck_files[0]

    drb_files = list(directory.parent.glob("*.drb"))
    if not drb_files:
        print("Warning: No .drb file found in parent directory", file=sys.stderr)
        sys.exit(1)
    drb = drb_files[0]
    return zcheck, drb


def get_paragraphs(spec_file: Path, yaml_file: Path) -> list[str]:
    """Extract paragraphs from YAML test file."""
    gramchecker = YamlGramChecker(config={"spec": spec_file, "test_file": None})

    yaml_content = yaml.load(yaml_file.read_text(), Loader=yaml.FullLoader)
    paragraphs: list[str] = sorted(
        {
            gramchecker.paragraph_to_testdata(gramchecker.make_error_markup(text))[0]
            for text in yaml_content.get("Tests", [])
            if text.strip()
        }
    )

    return paragraphs


def build_checker_command(zcheck: Path, variant: str = None) -> str:
    """Build divvun-checker command."""
    cmd = f"divvun-checker --archive {zcheck}"
    if variant:
        cmd += f" --variant {variant}"
    return cmd


def build_runtime_command(drb: Path, variant: str = None) -> str:
    """Build divvun-runtime command."""
    cmd = f"divvun-runtime run -p {drb}"
    if variant:
        # Map variant names if needed (e.g., smegram-dev -> sme-gram)
        pipeline = "sme-gram" if variant == "smegram" else variant
        cmd += f" -P {pipeline}"
    return cmd


@dataclass
class ComparisonStats:
    """Statistics for comparison results."""
    total_paragraphs: int = 0
    total_errors: int = 0
    exact_matches: int = 0
    typo_suggestion_order_diffs: int = 0
    extra_parenthesis_errors: int = 0
    other_mismatches: int = 0


def is_typo_suggestion_order_difference(
    checker_err: CheckerResult, 
    runtime_err: CheckerResult
) -> bool:
    """Check if the only difference is the order of typo suggestions.
    
    Args:
        checker_err: Error from divvun-checker
        runtime_err: Error from divvun-runtime
        
    Returns:
        True if errors match except for suggestion order
    """
    # Must be same error type
    if checker_err.err != runtime_err.err:
        return False
    
    # Must be typo errors
    if checker_err.err != "typo":
        return False
    
    # Must have same form and position
    if (checker_err.form != runtime_err.form or 
        checker_err.beg != runtime_err.beg or 
        checker_err.end != runtime_err.end):
        return False
    
    # Must have same suggestions, just different order
    return set(checker_err.rep) == set(runtime_err.rep)


def has_extra_parenthesis_errors(
    checker_errors: list[CheckerResult],
    runtime_errors: list[CheckerResult]
) -> tuple[bool, list[CheckerResult], list[CheckerResult]]:
    """Check if runtime has extra parenthesis-missing-space errors that checker doesn't.
    
    This is a known difference where divvun-runtime flags parentheses without spaces
    but divvun-checker doesn't.
    
    Args:
        checker_errors: Errors from divvun-checker
        runtime_errors: Errors from divvun-runtime
        
    Returns:
        Tuple of (has_extra_paren_errors, filtered_checker_errors, filtered_runtime_errors)
    """
    # Find parenthesis-missing-space errors in runtime
    paren_errors = [e for e in runtime_errors if e.err == "parenthesis-missing-space"]
    
    if not paren_errors:
        return False, checker_errors, runtime_errors
    
    # Filter out parenthesis errors from runtime for comparison
    runtime_without_paren = [e for e in runtime_errors if e.err != "parenthesis-missing-space"]
    
    # Check if the remaining errors match checker errors
    if len(checker_errors) == len(runtime_without_paren):
        return True, checker_errors, runtime_without_paren
    
    return False, checker_errors, runtime_errors


def compare_results(
    paragraph: str,
    checker_errors: list[CheckerResult],
    runtime_errors: list[CheckerResult],
    stats: ComparisonStats,
    verbose: bool = True,
    show_known: bool = False
) -> bool:
    """Compare results from checker and runtime. Returns True if they match exactly.
    
    Args:
        paragraph: The text being checked
        checker_errors: Errors from divvun-checker
        runtime_errors: Errors from divvun-runtime
        stats: Statistics object to update
        verbose: Whether to print detailed comparison
        show_known: Whether to show known differences in output
        
    Returns:
        True if results match exactly or have only known differences, False otherwise
    """
    stats.total_paragraphs += 1
    stats.total_errors += len(checker_errors)
    
    # Check for extra parenthesis errors (known difference)
    has_paren_diff, filtered_checker, filtered_runtime = has_extra_parenthesis_errors(
        checker_errors, runtime_errors
    )
    
    if has_paren_diff:
        # Runtime has extra parenthesis errors, but other errors might still match
        stats.extra_parenthesis_errors += 1
        if verbose and show_known:
            paren_errs = [e for e in runtime_errors if e.err == "parenthesis-missing-space"]
            print(f"\nKnown difference (extra parenthesis errors) for: {paragraph}")
            print(f"Runtime found {len(paren_errs)} extra parenthesis error(s):")
            for pe in paren_errs:
                print(f"  - '{pe.form}' at {pe.beg}-{pe.end}")
        
        # Continue comparing the filtered errors
        checker_errors = filtered_checker
        runtime_errors = filtered_runtime
    
    if len(checker_errors) != len(runtime_errors):
        stats.other_mismatches += 1
        if verbose:
            print(f"\nMismatch for: {paragraph}")
            print(f"Different number of errors: checker={len(checker_errors)}, runtime={len(runtime_errors)}")
            print("divvun-checker errors:")
            print(json.dumps([asdict(e) for e in checker_errors], indent=2, ensure_ascii=False))
            print("divvun-runtime errors:")
            print(json.dumps([asdict(e) for e in runtime_errors], indent=2, ensure_ascii=False))
        return False
    
    has_typo_order_diff = False
    has_unknown_difference = False
    
    for checker_err, runtime_err in zip(checker_errors, runtime_errors, strict=True):
        if checker_err == runtime_err:
            # Exact match
            continue
        elif is_typo_suggestion_order_difference(checker_err, runtime_err):
            # Known difference: typo suggestions in different order
            has_typo_order_diff = True
            if verbose and show_known:
                print(f"\nKnown difference (typo suggestion order) for: {paragraph}")
                print(f"Form: {checker_err.form} at {checker_err.beg}-{checker_err.end}")
                print(f"Checker suggestions: {checker_err.rep[:5]}...")
                print(f"Runtime suggestions: {runtime_err.rep[:5]}...")
        else:
            # Unknown difference
            has_unknown_difference = True
            if verbose:
                print(f"\nUnknown mismatch for: {paragraph}")
                print("divvun-checker error:")
                print(json.dumps(asdict(checker_err), indent=2, ensure_ascii=False))
                print("divvun-runtime error:")
                print(json.dumps(asdict(runtime_err), indent=2, ensure_ascii=False))
    
    if has_unknown_difference:
        stats.other_mismatches += 1
        return False
    elif has_typo_order_diff:
        stats.typo_suggestion_order_diffs += 1
        return True  # Consider it a match for overall statistics
    elif has_paren_diff:
        # Already counted above, just return True
        return True
    else:
        stats.exact_matches += 1
        return True


def engine_comparator(directory_name: str, variant: str = None, show_known: bool = False):
    """Compare divvun-checker and divvun-runtime outputs for all YAML files in directory.
    
    Args:
        directory_name: Path to directory containing YAML test files
        variant: Optional variant/pipeline name to use
        show_known: Whether to show known differences in output
    """
    directory = Path(directory_name)
    zcheck, drb = get_gramcheck_bundles(directory)

    checker_cmd = build_checker_command(zcheck, variant)
    runtime_cmd = build_runtime_command(drb, variant)
    
    print(f"Checker command: {checker_cmd}")
    print(f"Runtime command: {runtime_cmd}")
    print()

    stats = ComparisonStats()
    files_processed = 0

    for yaml_file in directory.glob("*.yaml"):
        print(f"Processing {yaml_file.name}...")
        files_processed += 1
        
        # Get test paragraphs
        paragraphs = get_paragraphs(zcheck, yaml_file)
        
        # Run both checkers in parallel
        checker_output = check_paragraphs_in_parallel(checker_cmd, paragraphs)
        runtime_output = check_paragraphs_in_parallel(runtime_cmd, paragraphs)
        
        # Parse outputs
        checker_results = parse_checker_output(checker_output)
        runtime_results = parse_checker_output(runtime_output)
        
        # Check if result counts match
        if len(checker_results) != len(paragraphs):
            print(f"ERROR: Checker returned {len(checker_results)} results for {len(paragraphs)} paragraphs", file=sys.stderr)
            continue
            
        if len(runtime_results) != len(paragraphs):
            print(f"ERROR: Runtime returned {len(runtime_results)} results for {len(paragraphs)} paragraphs", file=sys.stderr)
            continue
        
        # Compare results
        file_mismatches = 0
        file_known_diffs = 0
        for paragraph, checker_errs, runtime_errs in zip(
            paragraphs, checker_results, runtime_results, strict=True
        ):
            errors_before = stats.other_mismatches
            known_before = stats.typo_suggestion_order_diffs
            
            # Compare with verbose=False first
            matches = compare_results(paragraph, checker_errs, runtime_errs, stats, verbose=False, show_known=show_known)
            
            # Check what kind of difference we found
            if not matches:
                file_mismatches += 1
                # Show details for first few unknown mismatches
                if file_mismatches <= 3 and stats.other_mismatches > errors_before:
                    compare_results(paragraph, checker_errs, runtime_errs, stats, verbose=True, show_known=show_known)
            elif stats.typo_suggestion_order_diffs > known_before:
                file_known_diffs += 1
        
        # Report file results
        exact_matches = len(paragraphs) - file_mismatches - file_known_diffs
        if file_mismatches == 0:
            if file_known_diffs > 0:
                print(f"✓ {yaml_file.name}: {exact_matches} exact matches, {file_known_diffs} known differences (typo order)")
            else:
                print(f"✓ {yaml_file.name}: All {len(paragraphs)} paragraphs match exactly")
        else:
            print(f"✗ {yaml_file.name}: {file_mismatches} unknown mismatches, {file_known_diffs} known differences")
        print()
    
    print("=" * 70)
    print("Summary:")
    print(f"  Files processed:              {files_processed}")
    print(f"  Total paragraphs checked:     {stats.total_paragraphs}")
    print(f"  Total errors found:           {stats.total_errors}")
    print(f"  Exact matches:                {stats.exact_matches}")
    print("  Known differences:")
    print(f"    - Typo suggestion order:    {stats.typo_suggestion_order_diffs}")
    print(f"    - Extra parenthesis errors: {stats.extra_parenthesis_errors}")
    print(f"  Unknown mismatches:           {stats.other_mismatches}")
    print()
    
    total_known = stats.typo_suggestion_order_diffs + stats.extra_parenthesis_errors
    if stats.other_mismatches == 0:
        if total_known > 0:
            print(f"  ✓ Success! Only known differences found ({total_known} total)")
        else:
            print("  ✓ Perfect! All outputs match exactly!")
    else:
        print(f"  ✗ {stats.other_mismatches} unknown mismatches need investigation")
