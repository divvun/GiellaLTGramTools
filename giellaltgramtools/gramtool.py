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
#   Copyright © 2024 The University of Tromsø
#   http://giellatekno.uit.no & http://divvun.no
#
"""GiellaLT tools for grammarchecker needs."""

import sys
from pathlib import Path

import click
from yaml.scanner import ScannerError

from giellaltgramtools.comparator import engine_comparator
from giellaltgramtools.corpus_gramtest import CorpusGramTest
from giellaltgramtools.make_grammarchecker_zip import make_archive
from giellaltgramtools.yaml_gramtest import YamlGramTest


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
    Necessary argument for the xml command, useful for the yaml command when doing out of tree builds.""",
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
def yaml(
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
        tester = YamlGramTest(ctx.obj, Path(yaml_file))
        ret = tester.run()
        sys.stdout.write(str(tester))
        sys.exit(ret)
    except KeyboardInterrupt:
        sys.exit(130)
    except ScannerError as error:
        print(f"YAML Scanner Error in {yaml_file}:", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(99)


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
        tester = CorpusGramTest(ctx.obj, count_typos, targets)
        ret = tester.run()
        sys.stdout.write(str(tester))
        sys.exit(ret)
    except KeyboardInterrupt:
        sys.exit(130)


@main.command()
@click.argument("pipe_spec", type=click.Path(exists=True))
@click.argument("archive_name", type=click.Path())
def build_archive(pipe_spec: str, archive_name: str):
    """Build the grammar archive."""
    make_archive(pipe_spec, archive_name)


@main.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option(
    "-V",
    "--variant",
    help="Variant/pipeline to use for comparison",
)
@click.option(
    "--show-known",
    is_flag=True,
    help="Show known differences (typo order, parenthesis errors) in output",
)
def compare(directory: str, variant: str | None = None, show_known: bool = False):
    """Compare grammar checker results in a directory."""
    engine_comparator(directory, variant, show_known)
