# -*- coding:utf-8 -*-

# Copyright © 2020-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>

"""Write report on differences on manual markup and gramdivvun markup"""
import ctypes
import io
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from zipfile import ZipFile

from lxml import etree


def get_pipespecs(name: Path):
    def get_parsed():
        if name.suffix == ".zcheck":
            with ZipFile(name) as archive:
                with archive.open("pipespec.xml") as pipespec:
                    return etree.parse(pipespec)
        return etree.parse(name)

    parsed = get_parsed()
    return parsed.getroot().attrib["default-pipe"], parsed.xpath(".//pipeline/@name")


@contextmanager
def stderr_redirector(stream):
    """Catch errors from libdivvun"""
    libc = ctypes.CDLL(None)
    c_stderr = (
        ctypes.c_void_p.in_dll(libc, "__stderrp")
        if sys.platform == "darwin"
        else ctypes.c_void_p.in_dll(libc, "stderr")
    )

    # The original fd stdout points to. Usually 1 on POSIX systems.
    original_stderr_fd = sys.stderr.fileno()

    def _redirect_stderr(to_fd):
        """Redirect stderr to the given file descriptor."""
        # Flush the C-level buffer stderr
        libc.fflush(c_stderr)
        # Flush and close sys.stderr - also closes the file descriptor (fd)
        sys.stderr.close()
        # Make original_stderr_fd point to the same file as to_fd
        os.dup2(to_fd, original_stderr_fd)
        # Create a new sys.stderr that points to the redirected fd
        sys.stderr = io.TextIOWrapper(os.fdopen(original_stderr_fd, "wb"))

    # Save a copy of the original stderr fd in saved_stderr_fd
    saved_stderr_fd = os.dup(original_stderr_fd)
    try:
        # Create a temporary file and redirect stderr to it
        tfile = tempfile.TemporaryFile(mode="w+b")
        _redirect_stderr(tfile.fileno())
        # Yield to caller, then redirect stderr back to the saved fd
        yield
        _redirect_stderr(saved_stderr_fd)
        # Copy contents of temporary file to the given stream
        tfile.flush()
        tfile.seek(0, io.SEEK_SET)
        stream.write(tfile.read())
    finally:
        tfile.close()
        os.close(saved_stderr_fd)


COLORS = {
    "red": "\033[1;31m",
    "green": "\033[0;32m",
    "orange": "\033[0;33m",
    "yellow": "\033[1;33m",
    "blue": "\033[0;34m",
    "light_blue": "\033[0;36m",
    "reset": "\033[m",
}


def extract_correction(child):
    """Replace error element with correction attribute."""
    correct = child.find("./correct")
    parts = [correct.text if correct is not None and correct.text is not None else ""]
    if child.tail:
        parts.append(child.tail)

    return "".join(parts)


def colourise(string, *args, **kwargs):
    kwargs.update(COLORS)
    return string.format(*args, **kwargs)


# class UI(ArgumentParser):
#     def __init__(self):
#         super().__init__()
#         self.add_argument(
#             "-c",
#             "--colour",
#             dest="colour",
#             action="store_true",
#             help="Colours the output",
#         )
#         self.test = None

#     def start(self):
#         ret = self.test.run()
#         sys.stdout.write(str(self.test))
#         sys.exit(ret)


# class CorpusUI(UI):
#     def __init__(self):
#         super().__init__()
#         self.add_argument(
#             "--ignore-typos",
#             dest="ignore_typos",
#             action="store_true",
#             help="Pretend as if typos are correct",
#         )
#         self.add_argument("archive", help="The grammarchecker archive")
#         self.add_argument(
#             "targets",
#             nargs="+",
#             help="""Name of the file or directories to process.
#                         If a directory is given, all files in this directory
#                         and its subdirectories will be listed.""",
#         )

#         self.test = CorpusGramTest(self.parse_args())


# def main():
#     try:
#         ui = CorpusUI()
#         ui.start()
#     except KeyboardInterrupt:
#         sys.exit(130)
#     except Exception as error:
#         print(f"An error occurred: {error}")
#         raise SystemExit from error
