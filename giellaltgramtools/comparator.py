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
        pipeline = "sme-gram" if variant == "smegram-dev" else variant
        cmd += f" -P {pipeline}"
    return cmd


def compare_results(
    paragraph: str,
    checker_errors: list[CheckerResult],
    runtime_errors: list[CheckerResult],
    verbose: bool = True
) -> bool:
    """Compare results from checker and runtime. Returns True if they match."""
    if len(checker_errors) != len(runtime_errors):
        if verbose:
            print(f"\nMismatch for: {paragraph}")
            print(f"Different number of errors: checker={len(checker_errors)}, runtime={len(runtime_errors)}")
            print("divvun-checker errors:")
            print(json.dumps([asdict(e) for e in checker_errors], indent=2, ensure_ascii=False))
            print("divvun-runtime errors:")
            print(json.dumps([asdict(e) for e in runtime_errors], indent=2, ensure_ascii=False))
        return False
    
    for checker_err, runtime_err in zip(checker_errors, runtime_errors, strict=True):
        if checker_err != runtime_err:
            if verbose:
                print(f"\nMismatch for: {paragraph}")
                print("divvun-checker error:")
                print(json.dumps(asdict(checker_err), indent=2, ensure_ascii=False))
                print("divvun-runtime error:")
                print(json.dumps(asdict(runtime_err), indent=2, ensure_ascii=False))
            return False
    
    return True


def engine_comparator(directory_name: str, variant: str = None):
    """Compare divvun-checker and divvun-runtime outputs for all YAML files in directory.
    
    Args:
        directory_name: Path to directory containing YAML test files
        variant: Optional variant/pipeline name to use
    """
    directory = Path(directory_name)
    zcheck, drb = get_gramcheck_bundles(directory)

    checker_cmd = build_checker_command(zcheck, variant)
    runtime_cmd = build_runtime_command(drb, variant)
    
    print(f"Checker command: {checker_cmd}")
    print(f"Runtime command: {runtime_cmd}")
    print()

    total_files = 0
    total_paragraphs = 0
    total_mismatches = 0

    for yaml_file in directory.glob("*.yaml"):
        print(f"Processing {yaml_file.name}...")
        total_files += 1
        
        # Get test paragraphs
        paragraphs = get_paragraphs(zcheck, yaml_file)
        total_paragraphs += len(paragraphs)
        
        # Run both checkers in parallel (both now return same format thanks to runtime_parser)
        checker_output = check_paragraphs_in_parallel(checker_cmd, paragraphs)
        runtime_output = check_paragraphs_in_parallel(runtime_cmd, paragraphs)
        
        # Parse outputs
        checker_results = parse_checker_output(checker_output)
        runtime_results = parse_checker_output(runtime_output)
        
        # Compare results
        file_mismatches = 0
        for paragraph, checker_errs, runtime_errs in zip(
            paragraphs, checker_results, runtime_results, strict=True
        ):
            if not compare_results(paragraph, checker_errs, runtime_errs):
                file_mismatches += 1
                total_mismatches += 1
        
        if file_mismatches == 0:
            print(f"✓ {yaml_file.name}: All {len(paragraphs)} paragraphs match")
        else:
            print(f"✗ {yaml_file.name}: {file_mismatches}/{len(paragraphs)} mismatches")
        print()
    
    print("=" * 60)
    print("Summary:")
    print(f"  Files processed: {total_files}")
    print(f"  Total paragraphs: {total_paragraphs}")
    print(f"  Mismatches: {total_mismatches}")
    if total_mismatches == 0:
        print("  ✓ All outputs match!")
    else:
        print(f"  ✗ {total_mismatches} mismatches found")
