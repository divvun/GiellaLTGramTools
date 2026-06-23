# -*- coding: utf-8 -*-
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this file. If not, see <http://www.gnu.org/licenses/>.
#
#   Copyright © 2024-2026 The University of Tromsø
#   http://giellatekno.uit.no & http://divvun.no
#
"""GiellaLT tools for grammarchecker needs."""

import sys
from datetime import date
from pathlib import Path
from subprocess import CalledProcessError

import click

from giellaltgramtools.asr_gramcheck import asr_output_checker
from giellaltgramtools.candidates import create_yaml_candidates
from giellaltgramtools.comparator import engine_comparator
from giellaltgramtools.corpus_gramtest import CorpusGramTest
from giellaltgramtools.count_tests import report_test_counts
from giellaltgramtools.gramchecker import GrammarCheckerCommandError
from giellaltgramtools.make_grammarchecker_zip import make_archive
from giellaltgramtools.yaml_gramchecker import GramCheckerSentenceError
from giellaltgramtools.yaml_gramtest import YamlDuplicateError, YamlGramTest
from giellaltgramtools.yaml_test_file import YamlTestFileError


@click.group()
@click.version_option()
@click.pass_context
def main(ctx: click.Context):
    """Tool for working with GiellaLT grammars."""
    pass


@main.group()
@click.option("-c", "--colour", is_flag=True, help="Colours the output")
@click.option(
    "-p",
    "--hide-passes",
    help="Suppresses passes to make finding fails easier",
    is_flag=True,
)
@click.option(
    "-s",
    "--spec",
    help="""Path to the pipespec.xml spec, .zcheck file, .drb bundle, or .ts pipeline. 
    Necessary argument for the xml command, useful for the yaml command when doing out 
    of tree builds.""",
    type=click.Path(exists=True),
)
@click.option(
    "-V",
    "--variant",
    help="""Which variant should be used.""",
)
@click.option(
    "--use-runtime",
    is_flag=True,
    help="Use divvun-runtime instead of divvun-checker",
)
@click.pass_context
def test(  # noqa: PLR0913
    ctx: click.Context,
    colour: bool,
    hide_passes: bool,
    spec: str,
    variant: str,
    use_runtime: bool,
):
    """Test the grammars."""
    ctx.ensure_object(dict)
    ctx.obj = {
        "colour": colour,
        "hide_passes": hide_passes,
        "spec": spec,
        "variant": variant,
        "use_runtime": use_runtime,
    }


@test.command()
@click.argument("yaml_file", type=click.Path(exists=True))
@click.option(
    "-q",
    "--silent",
    help="Hide all output; exit code only",
    is_flag=True,
)
@click.option(
    "-o",
    "--output",
    default="normal",
    type=click.Choice(["normal", "final"]),
    help="Output style for the results",
)
@click.option(
    "--move-tests",
    is_flag=True,
    help="Move passing tests from FAIL files to PASS files",
)
@click.option(
    "--remove-dupes",
    is_flag=True,
    help="Remove duplicate tests from test files",
)
@click.pass_context
def yaml(  # noqa: PLR0913
    ctx: click.Context,
    silent: bool,
    output: str,
    move_tests: bool,
    remove_dupes: bool,
    yaml_file: str,
):
    """Test a YAML file."""
    ctx.ensure_object(dict)
    ctx.obj["output"] = "silent" if silent else output
    ctx.obj["move_tests"] = move_tests
    ctx.obj["remove_dupes"] = remove_dupes
    try:
        tester = YamlGramTest(ctx, Path(yaml_file))
        ret = tester.run()
        sys.stdout.write(str(tester))
        sys.exit(ret)
    except (
        GramCheckerSentenceError,
        YamlTestFileError,
        YamlDuplicateError,
        GrammarCheckerCommandError,
    ) as error:
        print(
            f"{error}",
            file=sys.stderr,
        )
        sys.exit(99)
    except KeyboardInterrupt:
        sys.exit(130)


@test.command()
@click.argument("targets", type=click.Path(exists=True), nargs=-1)
@click.option(
    "-t",
    "--count_typos",
    help="Also count typos as errors",
    default=True,
    is_flag=True,
)
@click.pass_context
def xml(ctx: click.Context, count_typos: bool, targets: list[str]):
    """Test XML files."""
    try:
        tester = CorpusGramTest(ctx, count_typos, targets)
        ret = tester.run()
        sys.stdout.write(str(tester))
        sys.exit(ret)
    except KeyboardInterrupt:
        sys.exit(130)
    except (GrammarCheckerCommandError, GramCheckerSentenceError) as error:
        print(
            str(error),
            file=sys.stderr,
        )
        sys.exit(1)


@main.command()
@click.argument("pipe_spec", type=click.Path(exists=True))
@click.argument("archive_name", type=click.Path())
def build_archive(pipe_spec: str, archive_name: str):
    """Build the grammar archive."""
    make_archive(pipe_spec, archive_name)


@main.command()
@click.argument("language")
def compare(language: str):
    """Compare divvun-checker and divvun-runtime test results."""
    engine_comparator(language)


@main.command()
@click.argument("test_directory", type=click.Path(exists=True))
def count_tests(test_directory: str):
    """Count the number of PASS and FAIL tests in a given directory."""
    report_test_counts(test_directory)


@main.command()
@click.argument("archive_path", type=click.Path(exists=True))
@click.option(
    "--candidate_prefix",
    type=str,
    default=date.today().strftime("%Y-%m-%d"),
    help="Prefix for the candidates file (default: today's date in YYYY-mm-dd)",
)
def create_candidates(
    archive_path: str,
    candidate_prefix: str,
):
    """Create candidate files for testing from stdin input only."""
    try:
        create_yaml_candidates(candidate_prefix, Path(archive_path))
    except (FileNotFoundError, CalledProcessError, GrammarCheckerCommandError) as error:
        print(
            f"Error creating candidates: {error}",
            file=sys.stderr,
        )
        sys.exit(1)


@main.command()
@click.argument("archive_path", type=click.Path(exists=True))
@click.argument("asr_file", type=click.Path(exists=True))
def gramcheck_asr_output(
    archive_path: str,
    asr_file: str,
):
    """Check ASR output against the grammar archive."""
    try:
        asr_output_checker(Path(asr_file), Path(archive_path))
    except (FileNotFoundError, CalledProcessError, GrammarCheckerCommandError) as error:
        print(
            f"Error checking ASR output: {error}",
            file=sys.stderr,
        )
        sys.exit(1)
