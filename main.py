#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# inPeDF - Leitor de documentos PDF
#
# Copyright (C) 2026 Heder Dorneles Soares
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# Author: Heder Dorneles Soares
# License: GPL-2.0-only
#

"""Ponto de entrada da aplicação inPeDF."""

import os
import sys


def main() -> int:
    """Inicializa e executa a aplicação."""
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "--usage", "--version"):
        import argparse
        from inpedf import __version__

        parser = argparse.ArgumentParser(
            prog="inpedf",
            usage="%(prog)s [PDF ...]\n       %(prog)s export [OPTIONS] PDF ...",
            description=(
                "PDF reader with text search and selection, bookmarks, printing, "
                "rotation and fullscreen presentations."
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=(
                "Commands:\n"
                "  export  Convert PDFs to Markdown, TXT and JSON without a graphical session.\n"
                "          Supports batches, page ranges, limited parallel processes,\n"
                "          cancellation and JSON result reports.\n\n"
                "Examples:\n"
                "  inpedf document.pdf\n"
                "  inpedf export document.pdf --format md,json --output-dir converted\n"
                "  inpedf export documents/*.pdf --jobs 4 --report report.json\n\n"
                "Detailed export options: inpedf export --help\n"
                "The desktop reader opens in the background and releases the terminal.\n"
                "Diagnostics: $XDG_STATE_HOME/inpedf/inpedf.log\n"
                "             (default: ~/.local/state/inpedf/inpedf.log).\n"
                "Desktop keyboard shortcuts are available in the application menu."
            ),
        )
        parser.add_argument("files", nargs="*", metavar="PDF", help="PDF files to open in the reader.")
        parser.add_argument("--usage", action="help", help="Show this help message and exit.")
        parser.add_argument("--version", action="version", version=f"inPeDF {__version__}")
        parser.parse_args(sys.argv[1:])
        return 0

    if len(sys.argv) > 1 and sys.argv[1] == "export":
        from inpedf.export_cli import main as export_main
        return export_main(sys.argv[2:])

    gui_child = os.environ.pop("_INPEDF_GUI_CHILD", None) == "1"
    has_option = len(sys.argv) > 1 and sys.argv[1].startswith("-") and sys.argv[1] != "--"
    if not gui_child and not has_option:
        return launch_gui()

    from inpedf.application import InPeDFApplication
    app = InPeDFApplication()
    return app.run(sys.argv)


def launch_gui() -> int:
    """Start the desktop reader in its own session with diagnostics in a log."""
    from pathlib import Path
    import subprocess

    state_home = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    log_directory = state_home / "inpedf"
    try:
        log_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        log_path = log_directory / "inpedf.log"
        descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, "ab") as log:
            subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env={**os.environ, "_INPEDF_GUI_CHILD": "1"},
            )
    except OSError as error:
        print(f"Unable to start inPeDF: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
