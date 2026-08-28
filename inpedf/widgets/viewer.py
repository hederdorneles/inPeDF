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

"""Widget responsável pela visualização de documentos PDF."""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

from ..i18n import _


class PDFViewer(Gtk.Stack):
    """Visualizador de páginas PDF."""

    def __init__(self):
        super().__init__()

        self.document = None
        self.page = None
        self.page_number = 0

        self.zoom = 1.0

        self.create_empty_view()
        self.create_document_view()

        self.set_visible_child_name("empty")

    def create_empty_view(self):
        """Cria a tela exibida quando nenhum PDF está aberto."""

        placeholder = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
        )

        placeholder.set_halign(Gtk.Align.CENTER)
        placeholder.set_valign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name(
            "x-office-document-symbolic"
        )

        icon.set_pixel_size(64)
        icon.add_css_class("dim-label")

        title = Gtk.Label(
            label=_("No document open")
        )

        title.add_css_class("title-2")

        description = Gtk.Label(
            label=_("Open a PDF file to begin.")
        )

        description.add_css_class("dim-label")

        open_button = Gtk.Button(
            label=_("Open PDF")
        )

        open_button.set_action_name(
            "app.open"
        )

        open_button.add_css_class(
            "suggested-action"
        )

        open_button.set_halign(
            Gtk.Align.CENTER
        )

        placeholder.append(icon)
        placeholder.append(title)
        placeholder.append(description)
        placeholder.append(open_button)

        self.add_named(
            placeholder,
            "empty",
        )

    def create_document_view(self):
        """Cria a área onde a página PDF será renderizada."""

        self.scrolled = Gtk.ScrolledWindow()

        self.scrolled.set_hexpand(True)
        self.scrolled.set_vexpand(True)

        self.drawing_area = Gtk.DrawingArea()

        self.drawing_area.set_halign(
            Gtk.Align.CENTER
        )

        self.drawing_area.set_valign(
            Gtk.Align.START
        )

        self.drawing_area.set_margin_top(24)
        self.drawing_area.set_margin_bottom(24)
        self.drawing_area.set_margin_start(24)
        self.drawing_area.set_margin_end(24)

        self.drawing_area.set_draw_func(
            self.on_draw
        )

        self.scrolled.set_child(
            self.drawing_area
        )

        self.add_named(
            self.scrolled,
            "document",
        )

    def set_document(self, document):
        """Define o documento exibido no visualizador."""

        self.document = document

        if not document.is_open:
            self.set_visible_child_name("empty")
            return

        self.show_page(0)

        self.set_visible_child_name(
            "document"
        )

    def show_page(self, page_number):
        """Exibe uma página do documento."""

        if self.document is None:
            return

        self.page = self.document.get_page(
            page_number
        )

        if self.page is None:
            return

        self.page_number = page_number

        width, height = self.page.get_size()

        width = int(width * self.zoom)
        height = int(height * self.zoom)

        self.drawing_area.set_content_width(
            width
        )

        self.drawing_area.set_content_height(
            height
        )

        self.drawing_area.queue_draw()

    def on_draw(self, drawing_area, cr, width, height):
        """Renderiza a página PDF usando Cairo."""

        if self.page is None:
            return

        # Fundo branco da página.
        cr.set_source_rgb(
            1.0,
            1.0,
            1.0,
        )

        cr.paint()

        cr.save()

        cr.scale(
            self.zoom,
            self.zoom,
        )

        self.page.render(cr)

        cr.restore()
