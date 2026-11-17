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

import sys


def main() -> int:
    """Inicializa e executa a aplicação."""
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "--usage"):
        import argparse

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
                "Desktop keyboard shortcuts are available in the application menu."
            ),
        )
        parser.add_argument("files", nargs="*", metavar="PDF", help="PDF files to open in the reader.")
        parser.add_argument("--usage", action="help", help="Show this help message and exit.")
        parser.parse_args(sys.argv[1:])
        return 0

    if len(sys.argv) > 1 and sys.argv[1] == "export":
        from inpedf.export_cli import main as export_main
        return export_main(sys.argv[2:])

    from inpedf.application import InPeDFApplication
    app = InPeDFApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
