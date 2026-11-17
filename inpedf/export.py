"""Streaming PDF text export shared by the command line and desktop UI.

Copyright (C) 2026 Heder Dorneles Soares
License: GPL-2.0-only
"""

from contextlib import ExitStack
import json
import os
from pathlib import Path
import re

FORMATS = ("md", "txt", "json")


def page_indices(specification, total):
    """Return selected zero-based pages, validating against this document."""
    if not specification or specification == "all":
        return range(total)
    selected = set()
    for part in specification.split(","):
        if not re.fullmatch(r"[1-9][0-9]*(?:-[1-9][0-9]*)?", part.strip()):
            raise ValueError("Use pages such as 1,3-5 or all.")
        limits = [int(value) for value in part.split("-")]
        first, last = limits[0], limits[-1]
        if first > last or last > total:
            raise ValueError(f"Page range {part} is outside this document ({total} pages).")
        selected.update(range(first - 1, last))
    return sorted(selected)


def markdown_text(text):
    """Keep extracted text literal instead of interpreting it as Markdown."""
    return re.sub(r"([\\`*_{}\[\]<>#+!|~-])", r"\\\1", text)


def write_document(document, source_uri, formats, staging, pages="all"):
    """Yield progress after writing each page to staging, without accumulating text."""
    selected = page_indices(pages, document.get_n_pages())
    if not selected:
        raise ValueError("This document has no pages.")
    source = {
        "uri": source_uri,
        "title": document.get_title(),
        "author": document.get_author(),
        "page_count": document.get_n_pages(),
    }
    staging = Path(staging)
    with ExitStack() as stack:
        streams = {
            fmt: stack.enter_context((staging / ("document." + fmt)).open("w", encoding="utf-8"))
            for fmt in formats
        }
        if "json" in streams:
            streams["json"].write('{"schema_version":1,"source":')
            json.dump(source, streams["json"], ensure_ascii=False)
            streams["json"].write(',"pages":[')
        for index, number in enumerate(selected):
            page = document.get_page(number)
            text = (page.get_text() or "").replace("\x00", "").strip()
            width, height = page.get_size()
            if "txt" in streams:
                streams["txt"].write(f"--- Page {number + 1} ---\n{text}\n\n")
            if "md" in streams:
                streams["md"].write(
                    f"<!-- inpedf:page={number + 1} -->\n## Page {number + 1}\n\n"
                    + markdown_text(text) + "\n\n"
                )
            if "json" in streams:
                if index:
                    streams["json"].write(",")
                json.dump({
                    "number": number + 1, "width_points": width, "height_points": height,
                    "text": text, "text_available": bool(text),
                }, streams["json"], ensure_ascii=False)
            yield index + 1, len(selected), number + 1, bool(text)
        if "json" in streams:
            streams["json"].write("]}\n")


def convert_file(source, formats, staging, pages="all", password=None):
    """Worker entry point. Import only Poppler, with no GTK or display connection."""
    import gi
    gi.require_version("Poppler", "0.18")
    from gi.repository import Poppler

    source = Path(source)
    document = Poppler.Document.new_from_file(source.as_uri(), password)
    empty_pages = []
    converted = 0
    for converted, total, number, has_text in write_document(
        document, source.as_uri(), formats, staging, pages
    ):
        if not has_text:
            empty_pages.append(number)
    return {"pages": converted, "pages_without_text": empty_pages}


def publish_outputs(staging, destinations, overwrite=False):
    """Publish complete files, rolling back this group on conflict or failure."""
    staging = Path(staging)
    published = []
    backups = {}
    try:
        for fmt, destination in destinations.items():
            destination = Path(destination)
            if destination.is_symlink() or (destination.exists() and not destination.is_file()):
                raise FileExistsError(f"Destination is not a regular file: {destination}")
            if overwrite and destination.exists():
                backup = staging / ("previous." + fmt)
                os.replace(destination, backup)
                backups[destination] = backup
            temporary = staging / ("document." + fmt)
            if overwrite:
                os.replace(temporary, destination)
            else:
                # An atomic no-overwrite operation, even when another exporter is running.
                os.link(temporary, destination)
            published.append(destination)
    except BaseException:
        for destination in reversed(published):
            destination.unlink(missing_ok=True)
        for destination, backup in backups.items():
            os.replace(backup, destination)
        raise
