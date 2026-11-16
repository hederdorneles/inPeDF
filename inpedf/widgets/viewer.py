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
from math import ceil, pi

import cairo
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Poppler", "0.18")

from gi.repository import GObject, Gdk, GLib, Gtk, Poppler

from ..i18n import _


class PDFViewer(Gtk.Stack):
    """PDF document viewer."""

    __gsignals__ = {
        "history-changed": (GObject.SignalFlags.RUN_FIRST, None, ()),
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

        self.back_history = []
        self.forward_history = []
        self.selection_scroll_id = 0
        self.drag_state = None
        self.page_render_cache = {}
        self.document = None
        self.page = None
        self.page_number = 0
        self.selection_start = None
        self.selection_end = None
        self.link_page = None
        self.page_links = []
        self.selected_text = ""
        self.search_highlight = None

        self.rotation = 0
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
        for area in (self.drawing_area, self.continuous_area):
            area.set_focusable(True)
            area.set_cursor_from_name("text")
            drag = Gtk.GestureDrag(button=1)
            drag.connect("drag-begin", self.on_selection_begin, area)
            drag.connect("drag-update", self.on_selection_update, area)
            drag.connect("drag-end", self.on_selection_end, area)
            drag.connect("cancel", self.on_selection_cancel)
            area.add_controller(drag)
            motion = Gtk.EventControllerMotion()
            motion.connect("motion", self.on_link_motion, area)
            motion.connect("leave", self.on_link_leave, area)
            area.add_controller(motion)
            keys = Gtk.EventControllerKey()
            keys.connect("key-pressed", self.on_selection_key)
            area.add_controller(keys)

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

        self.clear_selection()
        self.back_history.clear()
        self.forward_history.clear()
        self.emit("history-changed")
        self.link_page = None
        self.page_links = []
        self.page_render_cache.clear()
        self.rotation = 0
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

    def page_view_size(self, page):
        width, height = page.get_size()
        return (height, width) if self.rotation in (90, 270) else (width, height)

    def page_to_view(self, page, x, y):
        """Map top-left PDF coordinates to the rotated page."""
        width, height = page.get_size()
        if self.rotation == 90:
            return height - y, x
        if self.rotation == 180:
            return width - x, height - y
        if self.rotation == 270:
            return y, width - x
        return x, y

    def view_to_page(self, page, x, y):
        width, height = page.get_size()
        if self.rotation == 90:
            return y, height - x
        if self.rotation == 180:
            return width - x, height - y
        if self.rotation == 270:
            return width - y, x
        return x, y

    def rotate(self, clockwise=True):
        if self.document is None or not self.document.is_open:
            return
        self.clear_selection()
        self.set_search_highlight(None)
        self.rotation = (self.rotation + (90 if clockwise else -90)) % 360
        self.back_history.clear()
        self.forward_history.clear()
        self.emit("history-changed")
        if self.continuous:
            self.rebuild_continuous_view()
            self.reapply_fit_mode()
        self.go_to_page(self.page_number)

    def set_continuous(self, enabled):
        """Change the page layout while keeping the current page."""
        self.clear_selection()
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
                self.continuous_pages.append(self.page_view_size(page))
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

    def reading_position(self):
        if self.continuous:
            return (self.page_number,
                    self.continuous_horizontal.get_value(),
                    self.continuous_vertical.get_value() - self.page_offsets[self.page_number])
        return (self.page_number, self.scrolled.get_hadjustment().get_value(),
                self.scrolled.get_vadjustment().get_value())

    def remember_position(self):
        position = self.reading_position()
        if not self.back_history or self.back_history[-1] != position:
            self.back_history.append(position)
            del self.back_history[:-100]
        self.forward_history.clear()
        self.emit("history-changed")

    def navigate_to_page(self, number):
        if self.document is not None and 0 <= number < self.document.page_count:
            self.remember_position()
            self.go_to_page(number)

    def navigate_history(self, backwards):
        source = self.back_history if backwards else self.forward_history
        target = self.forward_history if backwards else self.back_history
        if not source:
            return
        target.append(self.reading_position())
        number, x, y = source.pop()
        self.go_to_page(number)
        if self.continuous:
            self.continuous_horizontal.set_value(x)
            self.scroll_to_continuous_page(number, y)
        else:
            self.scrolled.get_hadjustment().set_value(x)
            self.scrolled.get_vadjustment().set_value(y)
        self.emit("history-changed")

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

        self.clear_selection()
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
            width, height = self.page_view_size(self.page)

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

        width, height = self.page_view_size(self.page)

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

        page_width, _ = self.page_view_size(self.page)

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

        page_width, page_height = self.page_view_size(self.page)

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
    
    def stop_selection_scroll(self):
        if self.selection_scroll_id:
            GLib.source_remove(self.selection_scroll_id)
            self.selection_scroll_id = 0
        self.drag_state = None

    def on_selection_cancel(self, gesture, sequence):
        self.stop_selection_scroll()

    def selection_scroll_tick(self):
        if self.drag_state is None or not self.get_mapped():
            self.selection_scroll_id = 0
            return GLib.SOURCE_REMOVE
        area, dx, dy = self.drag_state
        origin_x, origin_y = self.drag_origin
        pointer_y = origin_y + dy
        adjustment = (self.continuous_vertical if self.continuous
                      else self.scrolled.get_vadjustment())
        viewport_y = pointer_y if self.continuous else pointer_y + 24 - adjustment.get_value()
        height = self.continuous_area.get_height() if self.continuous else self.scrolled.get_height()
        speed = 0
        if viewport_y < 32:
            speed = -min(30, max(4, (32 - viewport_y) / 3))
        elif viewport_y > height - 32:
            speed = min(30, max(4, (viewport_y - height + 32) / 3))
        previous = adjustment.get_value()
        adjustment.set_value(previous + speed)
        if not self.continuous:
            dy += adjustment.get_value() - previous
        if adjustment.get_value() != previous:
            self.on_selection_update(None, dx, dy, area)
        return GLib.SOURCE_CONTINUE

    def clear_selection(self):
        self.stop_selection_scroll()
        self.selection_start = None
        self.selection_end = None
        self.selected_text = ""
        self.drawing_area.queue_draw()
        self.continuous_area.queue_draw()

    def selection_point(self, area, x, y):
        """Convert pointer coordinates to page coordinates with a top-left origin."""
        if self.document is None or not self.document.is_open:
            return None
        if not self.continuous:
            number = self.page_number
            view_x, view_y = x / self.zoom, y / self.zoom
        else:
            document_y = y + self.continuous_vertical.get_value()
            number = max(0, bisect_right(self.page_offsets, document_y) - 1)
            view_width, _ = self.continuous_pages[number]
            canvas = max(area.get_width(), self.continuous_width)
            left = (canvas - view_width * self.zoom) / 2 - self.continuous_horizontal.get_value()
            view_x = (x - left) / self.zoom
            view_y = (document_y - self.page_offsets[number]) / self.zoom
        page = self.document.get_page(number)
        width, height = page.get_size()
        page_x, page_y = self.view_to_page(page, view_x, view_y)
        return number, max(0, min(width, page_x)), max(0, min(height, page_y))

    def on_selection_begin(self, gesture, x, y, area):
        area.grab_focus()
        if gesture is not None:
            gesture.set_state(Gtk.EventSequenceState.CLAIMED)
        self.clear_selection()
        self.drag_origin = (x, y)
        self.selection_start = self.selection_point(area, x, y)
        self.selection_end = self.selection_start

    def link_at(self, area, x, y):
        point = self.selection_point(area, x, y)
        if point is None:
            return None
        number, page_x, page_y = point
        page = self.document.get_page(number)
        width, height = page.get_size()
        if not (0 < page_x < width and 0 < page_y < height):
            return None
        if self.link_page != number:
            self.page_links = page.get_link_mapping()
            self.link_page = number
        for mapping in self.page_links:
            bounds = mapping.area
            if (bounds.x1 <= page_x <= bounds.x2
                    and bounds.y1 <= height - page_y <= bounds.y2):
                return mapping.action
        return None

    def on_link_motion(self, controller, x, y, area):
        area.set_cursor_from_name("pointer" if self.link_at(area, x, y) else "text")

    def on_link_leave(self, controller, area):
        area.set_cursor_from_name("text")

    def on_selection_end(self, gesture, dx, dy, area):
        self.on_selection_update(gesture, dx, dy, area)
        self.stop_selection_scroll()
        self.update_selected_text()
        if abs(dx) <= 4 and abs(dy) <= 4:
            x, y = self.drag_origin
            action = self.link_at(area, x, y)
            if action is not None:
                self.activate_link(action)

    def activate_link(self, action):
        if action.type == Poppler.ActionType.GOTO_DEST:
            destination = action.goto_dest.dest
            if destination and destination.type == Poppler.DestType.NAMED:
                destination = self.document.document.find_dest(destination.named_dest)
            if destination:
                self.navigate_to_page(destination.page_num - 1)
        elif action.type == Poppler.ActionType.URI and action.uri.uri:
            launcher = Gtk.UriLauncher.new(action.uri.uri)
            launcher.launch(self.get_root(), None, self.on_link_launched)

    def on_link_launched(self, launcher, result):
        try:
            launcher.launch_finish(result)
        except GLib.Error as error:
            if not error.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED):
                self.get_root().get_application().show_error(
                    _("Unable to open link"), str(error)
                )

    def selection_rectangle(self, number):
        if self.selection_start is None or self.selection_end is None:
            return None
        start, end = sorted(
            (self.selection_start, self.selection_end),
            key=lambda point: (point[0], point[2], point[1]),
        )
        if not start[0] <= number <= end[0] or start == end:
            return None
        width, height = self.document.get_page(number).get_size()
        rectangle = Poppler.Rectangle()
        rectangle.x1, rectangle.y1 = start[1:] if number == start[0] else (0, 0)
        rectangle.x2, rectangle.y2 = end[1:] if number == end[0] else (width, height)
        return rectangle

    def on_selection_update(self, gesture, dx, dy, area):
        if self.selection_start is None:
            return
        self.drag_state = (area, dx, dy)
        if gesture is not None and not self.selection_scroll_id:
            self.selection_scroll_id = GLib.timeout_add(30, self.selection_scroll_tick)
        x, y = self.drag_origin
        self.selection_end = self.selection_point(area, x + dx, y + dy)
        area.queue_draw()

    def update_selected_text(self):
        if self.selection_start is None or self.selection_end is None:
            self.selected_text = ""
            return
        parts = []
        first = min(self.selection_start[0], self.selection_end[0])
        last = max(self.selection_start[0], self.selection_end[0])
        for number in range(first, last + 1):
            rectangle = self.selection_rectangle(number)
            if rectangle is not None:
                text = self.document.get_page(number).get_selected_text(
                    Poppler.SelectionStyle.GLYPH, rectangle
                )
                if text:
                    parts.append(text)
        self.selected_text = "\n".join(parts)

    def on_selection_key(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.clear_selection()
            return True
        if state & Gdk.ModifierType.CONTROL_MASK and keyval in (Gdk.KEY_c, Gdk.KEY_C):
            self.update_selected_text()
            if self.selected_text:
                self.get_clipboard().set(self.selected_text)
                return True
        return False

    def set_search_highlight(self, rectangle):
        self.search_highlight = rectangle
        if rectangle is None:
            self.drawing_area.queue_draw()
            self.continuous_area.queue_draw()
            return

        _, height = self.page.get_size()
        corners = [
            self.page_to_view(self.page, x, y)
            for x in (rectangle.x1, rectangle.x2)
            for y in (height - rectangle.y2, height - rectangle.y1)
        ]
        left = min(x for x, y in corners) * self.zoom
        right = max(x for x, y in corners) * self.zoom
        top = min(y for x, y in corners) * self.zoom
        bottom = max(y for x, y in corners) * self.zoom
        if self.continuous:
            self.continuous_area.queue_draw()
            self.scroll_to_continuous_page(self.page_number, max(0, top - 24))
            page_width, _ = self.continuous_pages[self.page_number]
            canvas = max(self.continuous_area.get_width(), self.continuous_width)
            margin = (canvas - page_width * self.zoom) / 2
            self.continuous_horizontal.clamp_page(margin + left, margin + right)
        else:
            self.drawing_area.queue_draw()
            self.scrolled.get_vadjustment().clamp_page(24 + top, 24 + bottom)
            self.scrolled.get_hadjustment().clamp_page(24 + left, 24 + right)

    def on_draw(self, drawing_area, cr, width, height):
        """Renderiza a página PDF usando Cairo."""

        if self.page is not None:
            self.draw_page(cr, self.page, self.search_highlight, self.page_number)

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
            self.draw_page(cr, page, highlight, number)
            cr.restore()

    def draw_page(self, cr, page, rectangle, number):
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

        width, height = page.get_size()
        if self.rotation == 90:
            cr.translate(height, 0)
        elif self.rotation == 180:
            cr.translate(width, height)
        elif self.rotation == 270:
            cr.translate(0, width)
        cr.rotate(self.rotation * pi / 180)

        # Cache pixels rather than replaying recorded PDF font operations under rotation.
        scale = self.zoom * self.get_scale_factor()
        key = (number, scale)
        surface = self.page_render_cache.get(key)
        pixel_width = max(1, ceil(width * scale))
        pixel_height = max(1, ceil(height * scale))
        cache_limit = 64 * 1024 * 1024
        required_bytes = pixel_width * pixel_height * 4
        if surface is None and required_bytes <= cache_limit:
            while self.page_render_cache and (
                len(self.page_render_cache) >= 3
                or sum(image.get_stride() * image.get_height()
                       for image in self.page_render_cache.values()) + required_bytes > cache_limit
            ):
                self.page_render_cache.pop(next(iter(self.page_render_cache)))
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, pixel_width, pixel_height)
            surface.set_device_scale(scale, scale)
            page.render(cairo.Context(surface))
            self.page_render_cache[key] = surface

        if surface is None:
            page.render(cr)
        else:
            cr.set_source_surface(surface, 0, 0)
            cr.paint()

        selection = self.selection_rectangle(number)
        if selection is not None:
            region = page.get_selected_region(1.0, Poppler.SelectionStyle.GLYPH, selection)
            cr.set_source_rgba(0.2, 0.45, 0.9, 0.35)
            for index in range(region.num_rectangles()):
                bounds = region.get_rectangle(index)
                cr.rectangle(bounds.x, bounds.y, bounds.width, bounds.height)
            cr.fill()

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
