# -*- coding:utf-8 -*-

# Copyright © 2023-2024 UiT The Arctic University of Norway
# License: GPL3  # noqa: ERA001
# Author: Børre Gaup <borre.gaup@uit.no>
"""Make a grammarchecker zip archive without '-dev' variants"""
from zipfile import ZipFile

from lxml import etree


def get_pipespec(spec_file: str) -> etree.ElementTree:
    """Remove all '-dev' pipelines."""
    pipespec = etree.parse(spec_file)
    for pipeline in pipespec.iter("pipeline"):
        if pipeline.xpath(".//*[contains(@n, './')]"):
            parent = pipeline.getparent()
            if parent is not None:
                parent.remove(pipeline)

    return pipespec


def make_archive(specfile: str, archive_name: str)-> None:
    """Make grammarchecker archive without '-dev' variants."""
    pipespec = get_pipespec(specfile)
    with ZipFile(archive_name, "w") as archive_zip:
        archive_zip.writestr("pipespec.xml", etree.tostring(pipespec))

        for filename in {
            element.attrib.get("n") for element in pipespec.xpath(".//*[@n]")
        }:
            archive_zip.write(filename)
