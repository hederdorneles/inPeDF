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

from gi.repository import GObject, Gdk, Gtk

from ..i18n import _


class PDFViewer(Gtk.Stack):
    """PDF document viewer."""

    __gsignals__ = {
        "page-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (int,),
        ),

        "zoom-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (float,),
        ),
    }

    def __init__(self):
        super().__init__()

        self.document = None
        self.page = None
        self.page_number = 0

        self.zoom = 1.0
        self.fit_mode = None

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

        scroll_controller = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.VERTICAL
        )

        scroll_controller.set_propagation_phase(
            Gtk.PropagationPhase.CAPTURE
        )

        scroll_controller.connect(
            "scroll",
            self.on_scroll,
        )

        self.scrolled.add_controller(
            scroll_controller
        )

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

        self.go_to_page(0)

        self.set_visible_child_name(
            "document"
        )

    # def go_to_page(self, page_number):
    #     """Exibe uma página específica do documento."""

    #     if self.document is None:
    #         return

    #     if not self.document.is_open:
    #         return

    #     if page_number < 0:
    #         return

    #     if page_number >= self.document.page_count:
    #         return

    #     page = self.document.get_page(
    #         page_number
    #     )

    #     if page is None:
    #         return

    #     self.page = page
    #     self.page_number = page_number

    #     width, height = self.page.get_size()

    #     width = int(
    #         width * self.zoom
    #     )

    #     height = int(
    #         height * self.zoom
    #     )

    #     self.drawing_area.set_content_width(
    #         width
    #     )

    #     self.drawing_area.set_content_height(
    #         height
    #     )

    #     self.drawing_area.queue_draw()

    #     self.emit(
    #         "page-changed",
    #         self.page_number,
    #     )
    
    def go_to_page(self, page_number):
        """Display a specific page of the document."""

        if self.document is None:
            return

        if not self.document.is_open:
            return

        if page_number < 0:
            return

        if page_number >= self.document.page_count:
            return

        page = self.document.get_page(
            page_number
        )

        if page is None:
            return

        self.page = page
        self.page_number = page_number

        fit_mode = self.fit_mode

        if fit_mode == "width":
            self.fit_width()

        elif fit_mode == "page":
            self.fit_page()

        else:
            width, height = self.page.get_size()

            self.drawing_area.set_content_width(
                int(width * self.zoom)
            )

            self.drawing_area.set_content_height(
                int(height * self.zoom)
            )

            self.drawing_area.queue_draw()

        self.emit(
            "page-changed",
            self.page_number,
        )

    def next_page(self):
        """Go to the next page."""

        self.go_to_page(
            self.page_number + 1
        )

    def previous_page(self):
        """Go to the previous page."""

        self.go_to_page(
            self.page_number - 1
        )

    def set_zoom(self, zoom):
        """Set the document zoom level."""

        self.fit_mode = None

        if zoom < 0.25:
            zoom = 0.25

        if zoom > 4.0:
            zoom = 4.0

        if zoom == self.zoom:
            return

        self.zoom = zoom

        if self.page is None:
            return

        width, height = self.page.get_size()

        self.drawing_area.set_content_width(
            int(width * self.zoom)
        )

        self.drawing_area.set_content_height(
            int(height * self.zoom)
        )

        self.drawing_area.queue_draw()

        self.emit(
            "zoom-changed",
            self.zoom,
        )

    def zoom_in(self):
        """Increase the document zoom level."""

        self.set_zoom(
            self.zoom + 0.25
        )

    def zoom_out(self):
        """Decrease the document zoom level."""

        self.set_zoom(
            self.zoom - 0.25
        )

    def fit_width(self):
        """Fit the current page to the available width."""

        if self.page is None:
            return

        page_width, _ = self.page.get_size()

        available_width = (
            self.scrolled.get_width() - 48
        )

        if available_width <= 0:
            return

        zoom = available_width / page_width

        self.set_zoom(
            zoom
        )

        self.fit_mode = "width"

    def fit_page(self):
        """Fit the entire current page in the available area."""

        if self.page is None:
            return

        page_width, page_height = self.page.get_size()

        available_width = (
            self.scrolled.get_width() - 48
        )

        available_height = (
           self.scrolled.get_height() - 48
        )

        if available_width <= 0:
            return

        if available_height <= 0:
            return

        width_zoom = (
            available_width / page_width
        )

        height_zoom = (
            available_height / page_height
        )

        zoom = min(
            width_zoom,
            height_zoom,
        )

        self.set_zoom(
            zoom
        )

        self.fit_mode = "page"

    def reapply_fit_mode(self):
        """Reapply the active page fitting mode"""

        if self.fit_mode == "width":
            self.fit_width()

        elif self.fit_mode == "page":
            self.fit_page()

    def on_scroll(self, controller, dx, dy):
        """Handle Ctrl+scroll zoom."""

        state = controller.get_current_event_state()

        if not state & Gdk.ModifierType.CONTROL_MASK:
            return False

        if dy < 0:
            self.zoom_in()
        elif dy > 0:
            self.zoom_out()

        return True
    
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
