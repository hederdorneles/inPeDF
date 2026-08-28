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

"""Gerenciamento de documentos PDF."""

import gi

gi.require_version("Poppler", "0.18")

from gi.repository import Gio, Poppler


class PDFDocument:
    """Representa um documento PDF aberto."""

    def __init__(self):
        self.document = None
        self.file = None
        self.name = None

    @property
    def is_open(self):
        """Indica se existe um documento aberto."""
        return self.document is not None

    @property
    def page_count(self):
        """Retorna o número total de páginas."""
        if self.document is None:
            return 0

        return self.document.get_n_pages()

    def open(self, file):
        """Abre um arquivo PDF."""

        if not isinstance(file, Gio.File):
            file = Gio.File.new_for_path(str(file))

        uri = file.get_uri()

        self.document = Poppler.Document.new_from_file(
            uri,
            None,
        )

        self.file = file
        self.name = file.get_basename()

    def get_page(self, page_number):
        """Retorna uma página do documento."""

        if self.document is None:
            return None

        if page_number < 0 or page_number >= self.page_count:
            raise IndexError("Página fora dos limites do documento")

        return self.document.get_page(page_number)

    def close(self):
        """Fecha o documento atual."""

        self.document = None
        self.file = None
        self.name = None
