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

from bisect import bisect_right

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
        self.search_highlight = None

        self.zoom = 1.0
        self.fit_mode = None
        self.continuous = False
        self.continuous_pages = []
        self.page_offsets = []
        self.continuous_height = 0
        self.continuous_width = 0
        self.positioning = False

        self.create_empty_view()
        self.create_document_view()
        self.create_continuous_view()

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
        self.search_highlight = None
        if self.continuous:
            self.rebuild_continuous_view()

        if not document.is_open:
            self.set_visible_child_name("empty")
            return

        self.go_to_page(0)

        self.set_visible_child_name(
            "continuous" if self.continuous else "document"
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
    
    def create_continuous_view(self):
        """Keep the drawing surface the size of the visible viewport."""
        self.continuous_area = Gtk.DrawingArea(hexpand=True, vexpand=True)
        self.continuous_area.set_draw_func(self.draw_continuous_pages)
        self.continuous_area.connect("resize", self.on_continuous_resize)
        self.continuous_vertical = Gtk.Adjustment()
        self.continuous_horizontal = Gtk.Adjustment()
        self.continuous_vertical.connect("value-changed", self.on_scroll_position_changed)
        self.continuous_horizontal.connect("value-changed", self.redraw_continuous)

        grid = Gtk.Grid()
        grid.attach(self.continuous_area, 0, 0, 1, 1)
        grid.attach(Gtk.Scrollbar(orientation=Gtk.Orientation.VERTICAL,
                                  adjustment=self.continuous_vertical), 1, 0, 1, 1)
        grid.attach(Gtk.Scrollbar(orientation=Gtk.Orientation.HORIZONTAL,
                                  adjustment=self.continuous_horizontal), 0, 1, 1, 1)
        controller = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
        controller.connect("scroll", self.on_continuous_scroll)
        self.continuous_area.add_controller(controller)
        self.add_named(grid, "continuous")

    def set_continuous(self, enabled):
        """Change the page layout while keeping the current page."""
        self.continuous = enabled
        if enabled:
            self.rebuild_continuous_view()
        else:
            self.continuous_pages.clear()
            self.page_offsets.clear()

        if self.document is not None and self.document.is_open:
            self.set_visible_child_name("continuous" if enabled else "document")
            self.go_to_page(self.page_number)

    def rebuild_continuous_view(self):
        self.continuous_pages = []
        if self.document is not None:
            for number in range(self.document.page_count):
                page = self.document.get_page(number)
                self.continuous_pages.append(page.get_size())
        self.resize_continuous_pages()

    def resize_continuous_pages(self):
        self.page_offsets = []
        offset = 24
        widest = 0
        for width, height in self.continuous_pages:
            self.page_offsets.append(offset)
            offset += max(1, int(height * self.zoom)) + 12
            widest = max(widest, int(width * self.zoom))
        self.continuous_height = offset + 12 if self.page_offsets else 0
        self.continuous_width = widest + 48
        self.on_continuous_resize(
            self.continuous_area,
            self.continuous_area.get_width(),
            self.continuous_area.get_height(),
        )

    def on_continuous_resize(self, area, width, height):
        self.positioning = True
        for adjustment, content, viewport in (
            (self.continuous_vertical, self.continuous_height, height),
            (self.continuous_horizontal, self.continuous_width, width),
        ):
            adjustment.configure(
                adjustment.get_value(), 0, max(content, viewport), 40,
                max(40, viewport * 0.9), viewport,
            )
        self.positioning = False
        area.queue_draw()

    def redraw_continuous(self, adjustment):
        self.continuous_area.queue_draw()

    def scroll_to_continuous_page(self, number, offset=0):
        self.positioning = True
        self.continuous_vertical.set_value(self.page_offsets[number] + offset)
        self.positioning = False

    def on_continuous_scroll(self, controller, dx, dy):
        if self.on_scroll(controller, dx, dy):
            return True
        step = 40 if controller.get_unit() == Gdk.ScrollUnit.WHEEL else 1
        self.continuous_horizontal.set_value(self.continuous_horizontal.get_value() + dx * step)
        self.continuous_vertical.set_value(self.continuous_vertical.get_value() + dy * step)
        return True

    def on_scroll_position_changed(self, adjustment):
        self.redraw_continuous(adjustment)
        if self.positioning or not self.continuous or not self.page_offsets:
            return

        position = adjustment.get_value()
        page_number = max(0, bisect_right(self.page_offsets, position + 24) - 1)
        if position > 0 and position >= adjustment.get_upper() - adjustment.get_page_size():
            page_number = len(self.page_offsets) - 1

        if page_number != self.page_number:
            self.set_search_highlight(None)
            self.page_number = page_number
            self.page = self.document.get_page(page_number)
            self.emit("page-changed", page_number)

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

        self.set_search_highlight(None)
        self.page = page
        self.page_number = page_number

        if self.continuous:
            self.scroll_to_continuous_page(page_number)
            self.emit("page-changed", page_number)
            return

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

        previous_zoom = self.zoom
        self.zoom = zoom

        if self.continuous and self.page_offsets:
            position = self.continuous_vertical.get_value()
            offset = max(0, position - self.page_offsets[self.page_number])
            self.resize_continuous_pages()
            self.scroll_to_continuous_page(self.page_number, offset * zoom / previous_zoom)
            self.emit("zoom-changed", zoom)
            return

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

        viewport = self.continuous_area if self.continuous else self.scrolled
        available_width = viewport.get_width() - 48

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

        viewport = self.continuous_area if self.continuous else self.scrolled
        available_width = viewport.get_width() - 48

        available_height = (
           viewport.get_height() - 48
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
    
    def set_search_highlight(self, rectangle):
        self.search_highlight = rectangle
        if self.continuous and self.page_number < len(self.continuous_pages):
            _, height = self.continuous_pages[self.page_number]
            self.continuous_area.queue_draw()
            if rectangle is not None:
                self.scroll_to_continuous_page(
                    self.page_number, max(0, (height - rectangle.y2) * self.zoom - 24)
                )
            return

        self.drawing_area.queue_draw()
        if rectangle is not None:
            _, height = self.page.get_size()
            margin = self.drawing_area.get_margin_top()
            self.scrolled.get_vadjustment().clamp_page(
                margin + (height - rectangle.y2) * self.zoom,
                margin + (height - rectangle.y1) * self.zoom,
            )
            margin = self.drawing_area.get_margin_start()
            self.scrolled.get_hadjustment().clamp_page(
                margin + rectangle.x1 * self.zoom,
                margin + rectangle.x2 * self.zoom,
            )

    def on_draw(self, drawing_area, cr, width, height):
        """Renderiza a página PDF usando Cairo."""

        if self.page is not None:
            self.draw_page(cr, self.page, self.search_highlight)

    def draw_continuous_pages(self, area, cr, width, height):
        top = self.continuous_vertical.get_value()
        left = self.continuous_horizontal.get_value()
        canvas_width = max(width, self.continuous_width)
        first = max(0, bisect_right(self.page_offsets, top) - 1)
        for number in range(first, len(self.page_offsets)):
            y = self.page_offsets[number] - top
            if y >= height:
                break
            page_width, page_height = self.continuous_pages[number]
            scaled_width = page_width * self.zoom
            scaled_height = page_height * self.zoom
            if y + scaled_height <= 0:
                continue

            page = self.document.get_page(number)
            x = (canvas_width - scaled_width) / 2 - left
            cr.save()
            cr.rectangle(x, y, scaled_width, scaled_height)
            cr.clip()
            cr.translate(x, y)
            highlight = self.search_highlight if number == self.page_number else None
            self.draw_page(cr, page, highlight)
            cr.restore()

    def draw_page(self, cr, page, rectangle):
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

        page.render(cr)

        if rectangle is not None:
            _, page_height = page.get_size()
            # Poppler text rectangles use a bottom-left origin.
            cr.set_source_rgba(1.0, 0.76, 0.0, 0.4)
            cr.rectangle(
                rectangle.x1,
                page_height - rectangle.y2,
                rectangle.x2 - rectangle.x1,
                rectangle.y2 - rectangle.y1,
            )
            cr.fill()

        cr.restore()
