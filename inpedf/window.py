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

"""Janela principal da aplicação inPeDF."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Poppler", "0.18")

from gi.repository import Adw, Gio, GLib, Gtk, Poppler

from .i18n import _
from .widgets.viewer import PDFViewer


class MainWindow(Adw.ApplicationWindow):
    """Janela principal do leitor de PDF."""


    def __init__(self, application):
        super().__init__(application=application)

        self.settings = application.settings

        self.document_state = application.document_state
        self._document_state_save_id = None

        self.set_title("inPeDF")
        self.set_size_request(700, 450)

        self.restore_window_state()

        self.create_actions()

        application.set_accels_for_action(
            "win.previous-page",
            ["Page_Up"],
        )

        application.set_accels_for_action(
            "win.next-page",
            ["Page_Down"],
        )

        application.set_accels_for_action("win.find", ["<Ctrl>f"])

        self.build_ui()
        self.lookup_action("page-layout").change_state(GLib.Variant("s", "continuous"))

        self.connect(
            "close-request",
            self.on_close_request,
        )

        self.apply_sidebar_setting()

        self.settings.connect(
            "changed::sidebar-visible",
            self.on_sidebar_setting_changed,
        )

        self.connect(
            "realize",
            self.on_window_realize,
        )


    def restore_window_state(self):
        """Restore the saved window state."""

        width = self.settings.get_int(
            "window-width"
        )

        height = self.settings.get_int(
            "window-height"
        )

        self.set_default_size(
            width,
            height,
        )

        if self.settings.get_boolean(
            "window-maximized"
        ):
            self.maximize()


    def save_window_state(self):
        """Save the current window state."""

        width, height = self.get_default_size()

        self.settings.set_int(
            "window-width",
            width,
        )

        self.settings.set_int(
            "window-height",
            height,
        )

        self.settings.set_boolean(
            "window-maximized",
            self.is_maximized(),
        )


    def schedule_document_state_save(self):
        """Schedule saving the current document state."""

        if self._document_state_save_id is not None:
            GLib.source_remove(
                self._document_state_save_id
            )

        self._document_state_save_id = GLib.timeout_add(
            500,
            self.save_document_state,
        )


    def save_document_state(self):
        """Save the current document reading state."""

        self._document_state_save_id = None

        document = self.viewer.document

        if document is None:
            return False

        if not document.is_open:
            return False

        if document.file is None:
            return False

        self.document_state.set(
            document.file.get_uri(),
            self.viewer.page_number,
            self.viewer.zoom,
        )

        return False


    def flush_document_state(self):
        """Save pending reading state before switching or closing."""

        if self._document_state_save_id is not None:
            GLib.source_remove(self._document_state_save_id)
            self.save_document_state()


    def on_close_request(self, window):
        """Save application state before closing."""

        self.save_window_state()

        self.flush_document_state()

        return False


    def build_ui(self):
        """Constrói a interface principal."""
        self.toolbar_view = Adw.ToolbarView()

        self.set_content(
            self.toolbar_view
        )

        self.create_header_bar()
        self.create_search_bar()
        self.create_content()
        self.create_bottom_bar()


    def create_search_bar(self):
        """Add the document search controls below the header."""
        self.search_results = []
        self.search_index = 0
        self.search_bar = Gtk.SearchBar(show_close_button=True)
        controls = Gtk.Box(spacing=6)
        self.search_entry = Gtk.SearchEntry(placeholder_text=_("Find in PDF"))
        self.search_status = Gtk.Label()
        self.search_previous = Gtk.Button(
            icon_name="go-up-symbolic",
            tooltip_text=_("Previous result"),
        )
        self.search_next = Gtk.Button(
            icon_name="go-down-symbolic",
            tooltip_text=_("Next result"),
        )

        controls.append(self.search_entry)
        controls.append(self.search_previous)
        controls.append(self.search_next)
        controls.append(self.search_status)
        self.search_bar.set_child(controls)
        self.search_bar.connect_entry(self.search_entry)
        self.toolbar_view.add_top_bar(self.search_bar)

        self.search_entry.connect("activate", self.on_search)
        self.search_entry.connect("changed", self.clear_search)
        self.search_entry.connect("stop-search", self.close_search)
        self.search_previous.connect("clicked", self.move_search_result, -1)
        self.search_next.connect("clicked", self.move_search_result, 1)
        self.search_bar.connect("notify::search-mode-enabled", self.on_search_visibility_changed)
        self.search_previous.set_sensitive(False)
        self.search_next.set_sensitive(False)

    def on_find(self, action, parameter):
        self.search_bar.set_search_mode(True)
        self.search_entry.grab_focus()

    def close_search(self, entry):
        self.search_bar.set_search_mode(False)

    def on_search_visibility_changed(self, bar, parameter):
        if not bar.get_search_mode():
            self.clear_search()

    def clear_search(self, entry=None):
        self.search_results.clear()
        self.search_index = 0
        self.search_previous.set_sensitive(False)
        self.search_next.set_sensitive(False)
        self.search_status.set_text("")
        self.viewer.set_search_highlight(None)

    def on_search(self, entry):
        """Find the query across all pages, or advance on repeated Enter."""
        if self.search_results:
            self.move_search_result(None, 1)
            return

        query = entry.get_text().strip()
        document = self.viewer.document
        if not query or document is None:
            return

        for page_number in range(document.page_count):
            page = document.get_page(page_number)
            self.search_results.extend(
                (page_number, rectangle) for rectangle in page.find_text(query)
            )

        if not self.search_results:
            self.search_status.set_text(_("No results"))
            return

        self.search_previous.set_sensitive(len(self.search_results) > 1)
        self.search_next.set_sensitive(len(self.search_results) > 1)
        self.show_search_result()

    def move_search_result(self, button, direction):
        self.search_index = (self.search_index + direction) % len(self.search_results)
        self.show_search_result()

    def show_search_result(self):
        page_number, rectangle = self.search_results[self.search_index]
        if page_number != self.viewer.page_number:
            self.viewer.go_to_page(page_number)
        self.viewer.set_search_highlight(rectangle)
        self.search_status.set_text(
            _("{current} of {total}").format(
                current=self.search_index + 1,
                total=len(self.search_results),
            )
        )

    def create_header_bar(self):
        """Cria a barra superior."""
        self.header_bar = Adw.HeaderBar()

        self.toolbar_view.add_top_bar(
            self.header_bar
        )

        title = Gtk.Label(
            label="inPeDF"
        )

        title.add_css_class("title")

        self.header_bar.set_title_widget(
            title
        )

        open_button = Gtk.Button(
            icon_name="document-open-symbolic",
            tooltip_text=_("Open document"),
        )

        open_button.set_action_name(
            "app.open"
        )

        self.header_bar.pack_start(
            open_button
        )

        self.sidebar_button = Gtk.ToggleButton(
            icon_name="sidebar-show-symbolic",
            tooltip_text=_(
                "Show or hide sidebar"
            ),
        )

        self.sidebar_button.set_active(True)

        self.sidebar_button.connect(
            "toggled",
            self.on_sidebar_toggled,
        )

        self.header_bar.pack_start(
            self.sidebar_button
        )

        zoom_out_button = Gtk.Button(
            icon_name="zoom-out-symbolic",
            tooltip_text=_("Zoom out"),
        )

        zoom_out_button.set_action_name(
            "win.zoom-out"
        )

        zoom_in_button = Gtk.Button(
            icon_name="zoom-in-symbolic",
            tooltip_text=_("Zoom in"),
        )

        zoom_in_button.set_action_name(
            "win.zoom-in"
        )

        self.header_bar.pack_end(
            zoom_in_button
        )

        self.header_bar.pack_end(
            zoom_out_button
        )

        self.menu_button = Gtk.MenuButton(
            icon_name="open-menu-symbolic",
            tooltip_text=_("Main menu"),
        )

        self.menu_button.set_menu_model(
            self.create_menu()
        )

        self.header_bar.pack_end(
            self.menu_button
        )


    def create_actions(self):
        """Create window actions."""

        layout = Gio.SimpleAction.new_stateful(
            "page-layout", GLib.VariantType.new("s"), GLib.Variant("s", "single")
        )
        layout.connect("change-state", self.on_page_layout_changed)
        self.add_action(layout)

        self.find_action = Gio.SimpleAction.new("find", None)
        self.find_action.connect("activate", self.on_find)
        self.find_action.set_enabled(False)
        self.add_action(self.find_action)

        self.previous_page_action = Gio.SimpleAction.new(
            "previous-page",
            None,
        )

        self.previous_page_action.connect(
            "activate",
            self.on_previous_page,
        )

        self.previous_page_action.set_enabled(
            False
        )

        self.add_action(
            self.previous_page_action
        )

        self.next_page_action = Gio.SimpleAction.new(
            "next-page",
            None,
        )

        self.next_page_action.connect(
            "activate",
            self.on_next_page,
        )

        self.next_page_action.set_enabled(
            False
        )

        self.add_action(
            self.next_page_action
        )

        self.zoom_out_action = Gio.SimpleAction.new(
            "zoom-out",
            None,
        )

        self.zoom_out_action.connect(
            "activate",
            self.on_zoom_out,
        )

        self.zoom_out_action.set_enabled(
            False
        )

        self.add_action(
            self.zoom_out_action
        )

        self.zoom_in_action = Gio.SimpleAction.new(
            "zoom-in",
            None,
        )

        self.zoom_in_action.connect(
            "activate",
            self.on_zoom_in,
        )

        self.zoom_in_action.set_enabled(
            False
        )

        self.add_action(
            self.zoom_in_action
        )

        self.fit_width_action = Gio.SimpleAction.new(
            "fit-width",
            None,
        )

        self.fit_width_action.connect(
            "activate",
            self.on_fit_width,
        )

        self.fit_width_action.set_enabled(
            False
        )

        self.add_action(
            self.fit_width_action
        )

        self.fit_page_action = Gio.SimpleAction.new(
            "fit-page",
            None,
        )

        self.fit_page_action.connect(
            "activate",
            self.on_fit_page,
        )

        self.fit_page_action.set_enabled(
            False
        )

        self.add_action(
            self.fit_page_action
        )


    def on_page_layout_changed(self, action, value):
        mode = value.get_string()
        if mode in ("single", "continuous") and value != action.get_state():
            self.viewer.set_continuous(mode == "continuous")
            action.set_state(value)
            self.continuous_button.set_active(mode == "continuous")

    def on_continuous_toggled(self, button):
        mode = "continuous" if button.get_active() else "single"
        self.lookup_action("page-layout").change_state(GLib.Variant("s", mode))

    def on_previous_page(self, action, parameter):
        """Go to the previous page."""
        
        self.viewer.previous_page()


    def on_next_page(self, action, parameter):
        """Go to the next page."""

        self.viewer.next_page()


    def on_zoom_out(self, action, parameter):
        """Decrease the document zoom level."""

        self.viewer.zoom_out()


    def on_zoom_in(self, action, parameter):
        """Increase the document zoom level."""

        self.viewer.zoom_in()


    def on_fit_width(self, action, parameter):
        """Fit the current page to the available width."""

        self.viewer.fit_width()


    def on_fit_page(self, action, parameter):
        """Fit the current page in the available area."""

        self.viewer.fit_page()


    def on_window_realize(self, window):
        """Connect to surface layout changes."""

        surface = self.get_surface()

        if surface is None:
            return

        surface.connect(
            "layout",
            self.on_surface_layout,
        )


    def on_surface_layout(self, surface, width, height):
        """Reapply the active fit mode after a surface resize."""

        GLib.idle_add(
            self.reapply_fit_mode
        )


    def reapply_fit_mode(self):
        """Reapply the viewer fit mode after layout."""

        self.viewer.reapply_fit_mode()

        return False

    
    def on_page_changed(self, viewer, page_number):
        """Update page information and navigation actions."""

        if viewer.document is None:
            return

        total_pages = viewer.document.page_count
        current_page = page_number + 1
        selection = self.thumbnails_view.get_model()
        if selection is not None:
            selection.set_selected(page_number)

        self.page_adjustment.set_upper(
            max(1, total_pages)
        )

        self.page_spin.set_value(
            current_page
        )

        self.page_spin.set_sensitive(
            total_pages > 0
        )

        self.page_total_label.set_text(
            _("of {total}").format(
                total=total_pages,
            )
        )

        self.previous_page_action.set_enabled(
            page_number > 0
        )

        self.next_page_action.set_enabled(
            page_number < total_pages - 1
        )

        self.schedule_document_state_save()


    def on_zoom_changed(self, viewer, zoom):
        """Update zoom information and action states."""

        zoom_percent = int(
            round(zoom * 100)
        )

        self.zoom_label.set_text(
            f"{zoom_percent}%"
        )

        self.zoom_out_action.set_enabled(
            zoom > 0.25
        )

        self.zoom_in_action.set_enabled(
            zoom < 4.0
        )

        self.schedule_document_state_save()


    def on_page_spin_changed(self, spin_button):
        """Go to the page selected in the page control."""

        if self.viewer.document is None:
            return

        page_number = (
            spin_button.get_value_as_int() - 1
        )

        if page_number == self.viewer.page_number:
            return

        self.viewer.go_to_page(
            page_number
        )


    def create_content(self):
        """Create the central area."""
        self.paned = Gtk.Paned(
            orientation=Gtk.Orientation.HORIZONTAL,
        )

        self.paned.set_position(240)

        self.toolbar_view.set_content(
            self.paned
        )

        self.sidebar = self.create_sidebar()

        self.paned.set_start_child(
            self.sidebar
        )

        self.paned.set_resize_start_child(
            False
        )

        self.paned.set_shrink_start_child(
            False
        )

        self.viewer = PDFViewer()

        self.viewer.connect(
            "page-changed",
            self.on_page_changed,
        )

        self.viewer.connect(
            "zoom-changed",
            self.on_zoom_changed,
        )

        self.paned.set_end_child(
            self.viewer
        )

        self.paned.set_resize_end_child(
            True
        )

        self.paned.set_shrink_end_child(
            False
        )


    def create_sidebar(self):
        """Cria a barra lateral."""
        container = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=0,
        )

        container.set_size_request(
            220,
            -1,
        )

        stack = Gtk.Stack()
        stack.set_vexpand(True)

        pages = self.create_thumbnails_panel()

        outline = self.create_outline_panel()

        annotations = self.create_annotations_panel()

        stack.add_titled(
            pages,
            "pages",
            _("Pages"),
        )

        stack.add_titled(
            outline,
            "outline",
            _("Outline"),
        )

        stack.add_titled(
            annotations,
            "annotations",
            _("Annotations"),
        )

        self.sidebar_stack = stack
        stack.connect("notify::visible-child-name", self.on_sidebar_tab_changed)

        switcher = Gtk.StackSwitcher()

        switcher.set_stack(stack)
        switcher.set_halign(Gtk.Align.CENTER)

        switcher.set_margin_top(6)
        switcher.set_margin_bottom(6)
        switcher.set_margin_start(6)
        switcher.set_margin_end(6)

        container.append(switcher)
        container.append(Gtk.Separator())
        container.append(stack)

        return container


    def create_thumbnails_panel(self):
        """Create a virtualized list that renders thumbnails as rows appear."""
        self.thumbnails_panel = Gtk.Stack()
        self.thumbnails_panel.add_named(
            self.create_sidebar_placeholder(_("Page thumbnails")),
            "empty",
        )

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self.setup_thumbnail)
        factory.connect("bind", self.bind_thumbnail)
        self.thumbnails_view = Gtk.ListView(
            factory=factory,
            single_click_activate=True,
        )
        self.thumbnails_view.connect("activate", self.on_thumbnail_activated)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(self.thumbnails_view)
        self.thumbnails_panel.add_named(scrolled, "pages")
        self.thumbnails_panel.set_visible_child_name("empty")
        return self.thumbnails_panel

    def setup_thumbnail(self, factory, item):
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content.set_margin_top(8)
        content.set_margin_bottom(8)
        preview = Gtk.DrawingArea(content_width=112, content_height=144)
        preview.set_halign(Gtk.Align.CENTER)
        content.append(preview)
        content.append(Gtk.Label())
        item.set_child(content)

    def bind_thumbnail(self, factory, item):
        content = item.get_child()
        content.get_last_child().set_text(item.get_item().get_string())
        preview = content.get_first_child()
        preview.set_draw_func(self.draw_thumbnail, item.get_position())
        preview.queue_draw()

    def draw_thumbnail(self, area, cr, width, height, position):
        document = self.viewer.document
        if document is None or position >= document.page_count:
            return

        page = document.get_page(position)
        page_width, page_height = page.get_size()
        if page_width <= 0 or page_height <= 0:
            return

        scale = min(width / page_width, height / page_height)
        cr.translate((width - page_width * scale) / 2, (height - page_height * scale) / 2)
        cr.scale(scale, scale)
        cr.rectangle(0, 0, page_width, page_height)
        cr.clip()
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        page.render(cr)

    def update_thumbnails(self, document):
        pages = Gtk.StringList.new(
            [str(number) for number in range(1, document.page_count + 1)]
        )
        selection = Gtk.SingleSelection(model=pages)
        selection.set_selected(self.viewer.page_number)
        self.thumbnails_view.set_model(selection)
        self.thumbnails_panel.set_visible_child_name("pages" if document.page_count else "empty")

    def on_thumbnail_activated(self, view, position):
        self.viewer.go_to_page(position)

    def create_annotations_panel(self):
        """Create the read-only list of annotations embedded in the PDF."""
        self.annotations_loaded = False
        self.annotations_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.annotations_list.set_placeholder(
            self.create_sidebar_placeholder(_("This PDF has no annotations"))
        )
        self.annotations_list.connect("row-activated", self.on_annotation_activated)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(self.annotations_list)
        return scrolled

    def reset_annotations(self):
        """Clear entries from the previous PDF and refresh the visible tab."""
        while row := self.annotations_list.get_first_child():
            self.annotations_list.remove(row)
        self.annotations_loaded = False
        self.on_sidebar_tab_changed(self.sidebar_stack, None)

    def on_sidebar_tab_changed(self, stack, parameter):
        """Read annotation mappings when the user first opens the tab."""
        if self.annotations_loaded or stack.get_visible_child_name() != "annotations":
            return

        document = self.viewer.document
        if document is None:
            return

        excluded_types = (
            Poppler.AnnotType.LINK,
            Poppler.AnnotType.POPUP,
            Poppler.AnnotType.WIDGET,
        )
        for page_number in range(document.page_count):
            page = document.get_page(page_number)
            for mapping in page.get_annot_mapping():
                annotation = mapping.annot
                if annotation.get_annot_type() in excluded_types:
                    continue

                contents = (annotation.get_contents() or "").strip()
                row = Adw.ActionRow(
                    title=_("Page {number}").format(number=page_number + 1),
                    use_markup=False,
                    activatable=True,
                )
                row.set_subtitle(contents or _("Annotation"))
                row.page_number = page_number
                self.annotations_list.append(row)

        self.annotations_loaded = True

    def on_annotation_activated(self, list_box, row):
        self.viewer.go_to_page(row.page_number)

    def create_outline_panel(self):
        """Create the sidebar tree and its empty state."""
        self.outline_panel = Gtk.Stack()
        self.outline_empty = self.create_sidebar_placeholder(_("Document outline"))
        self.outline_panel.add_named(self.outline_empty, "empty")

        self.outline_model = Gtk.TreeStore(str, int)
        self.outline_tree = Gtk.TreeView(
            model=self.outline_model,
            headers_visible=False,
            activate_on_single_click=True,
        )
        self.outline_tree.append_column(
            Gtk.TreeViewColumn(_("Outline"), Gtk.CellRendererText(), text=0)
        )
        self.outline_tree.connect("row-activated", self.on_outline_activated)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.outline_tree)
        self.outline_panel.add_named(scrolled, "tree")
        self.outline_panel.set_visible_child_name("empty")
        return self.outline_panel

    def update_outline(self, document):
        """Replace the outline with the chapters of the opened PDF."""
        self.outline_model.clear()
        try:
            index = Poppler.IndexIter.new(document.document)
        except TypeError:
            # PyGObject raises when Poppler returns NULL for a missing outline.
            index = None
        if index is None:
            self.outline_empty.set_text(_("This PDF has no outline"))
            self.outline_panel.set_visible_child_name("empty")
            return

        self.append_outline_entries(document, index)
        self.outline_panel.set_visible_child_name("tree")

    def append_outline_entries(self, document, index, parent=None):
        """Add sibling entries and preserve their nested sections."""
        while True:
            action = index.get_action()
            page = -1
            if action.type == Poppler.ActionType.GOTO_DEST:
                destination = action.goto_dest.dest
                if destination and destination.type == Poppler.DestType.NAMED:
                    destination = document.document.find_dest(destination.named_dest)
                if destination and 1 <= destination.page_num <= document.page_count:
                    page = destination.page_num - 1

            row = self.outline_model.append(parent, (action.any.title or "", page))
            child = index.get_child()
            if child is not None:
                self.append_outline_entries(document, child, row)
                if index.is_open():
                    self.outline_tree.expand_row(self.outline_model.get_path(row), False)

            if not index.next():
                break

    def on_outline_activated(self, tree, path, column):
        page = self.outline_model[path][1]
        if page >= 0:
            self.viewer.go_to_page(page)

    def create_sidebar_placeholder(self, text):
        """Cria um conteúdo temporário da barra lateral."""
        label = Gtk.Label(
            label=text
        )

        label.add_css_class(
            "dim-label"
        )

        label.set_margin_top(20)
        label.set_margin_start(12)
        label.set_margin_end(12)

        return label


    def create_bottom_bar(self):
        """Create the bottom navigation bar."""

        bar = Gtk.ActionBar()

        previous_button = Gtk.Button(
            icon_name="go-previous-symbolic",
            tooltip_text=_("Previous page"),
        )

        previous_button.set_action_name(
            "win.previous-page"
        )

        next_button = Gtk.Button(
            icon_name="go-next-symbolic",
            tooltip_text=_("Next page"),
        )

        next_button.set_action_name(
            "win.next-page"
        )

        bar.pack_start(
            previous_button
        )

        bar.pack_start(
            next_button
        )

        self.continuous_button = Gtk.ToggleButton(
            icon_name="view-list-symbolic",
            tooltip_text=_("Continuous"),
        )
        self.continuous_button.connect("toggled", self.on_continuous_toggled)
        bar.pack_start(self.continuous_button)

        page_text = Gtk.Label(
            label=_("Page")
        )

        bar.pack_start(
            page_text
        )

        self.page_adjustment = Gtk.Adjustment(
            value=1,
            lower=1,
            upper=1,
            step_increment=1,
            page_increment=1,
        )

        self.page_spin = Gtk.SpinButton(
            adjustment=self.page_adjustment,
            climb_rate=1,
            digits=0,
        )

        self.page_spin.set_numeric(True)
        self.page_spin.set_width_chars(4)
        self.page_spin.set_sensitive(False)

        self.page_spin.connect(
            "value-changed",
            self.on_page_spin_changed,
        )


        bar.pack_start(
            self.page_spin
        )

        self.page_total_label = Gtk.Label(
            label=_("of -")
        )

        bar.pack_start(
            self.page_total_label
        )

        self.zoom_label = Gtk.Label(
            label="100%"
        )

        self.zoom_label.add_css_class(
            "dim-label"
        )

        bar.pack_end(
            self.zoom_label
        )

        self.toolbar_view.add_bottom_bar(
            bar
        )

    

    def on_sidebar_toggled(self, button):
        """Show or hide the sidebar."""

        visible = button.get_active()

        self.sidebar.set_visible(
            visible
        )

        if ( self.settings.get_boolean("sidebar-visible") != visible ):
            self.settings.set_boolean(
                "sidebar-visible",
                visible,
            )   


    def apply_sidebar_setting(self):
        """Apply the configured sidebar visibility."""

        visible = self.settings.get_boolean(
            "sidebar-visible"
        )

        self.sidebar_button.set_active(
            visible
        )

        self.sidebar.set_visible(
            visible
        )


    def on_sidebar_setting_changed(self, settings, key):
        """Update the sidebar when its setting changes."""

        visible = settings.get_boolean(
            "sidebar-visible"
        )

        if self.sidebar_button.get_active() != visible:
            self.sidebar_button.set_active(
                visible
            )

        self.sidebar.set_visible(
            visible
        )
    

    def create_menu(self):
        """Create the main application menu."""

        menu = Gio.Menu()

        file_section = Gio.Menu()

        file_section.append(
            _("Open…"),
            "app.open",
        )

        recent_items = (
            self.get_application()
            .recent_files
            .get_items()
        )

        recent_menu = Gio.Menu()

        if recent_items:
            for recent in recent_items:
                item = Gio.MenuItem.new(
                    recent["name"],
                    None,
                )

                item.set_action_and_target_value(
                    "app.open-recent",
                    GLib.Variant(
                        "s",
                        recent["uri"],
                    ),
                )

                recent_menu.append_item(
                    item
                )

        else:
            recent_menu.append(
                _("No recent files"),
                None,
            )

        file_section.append_submenu(
            _("Recent files"),
            recent_menu,
        )

        menu.append_section(
            None,
            file_section,
        )

        view_section = Gio.Menu()
        layouts = Gio.Menu()
        layouts.append(_("Single page"), "win.page-layout::single")
        layouts.append(_("Continuous"), "win.page-layout::continuous")
        view_section.append_submenu(_("View mode"), layouts)

        view_section.append(
            _("Fit width"),
            "win.fit-width",
        )

        view_section.append(
            _("Fit page"),
            "win.fit-page",
        )

        menu.append_section(
            None,
            view_section,
        )

        application_section = Gio.Menu()

        application_section.append(
            _("Preferences"),
            "app.preferences",
        )

        application_section.append(
            _("About inPeDF"),
            "app.about",
        )

        menu.append_section(
            None,
            application_section,
        )

        quit_section = Gio.Menu()

        quit_section.append(
            _("Quit"),
            "app.quit",
        )

        menu.append_section(
            None,
            quit_section,
        )

        return menu


    def refresh_menu(self):
        """Refresh the main application menu."""

        self.menu_button.set_menu_model(
            self.create_menu()
        )


    def load_document(self, document):
        """Display a PDF document in the window."""

        self.clear_search()
        self.search_entry.set_text("")
        self.viewer.fit_mode = None
        self.thumbnails_view.set_model(None)
        self.viewer.set_document(document)
        self.find_action.set_enabled(True)
        self.update_outline(document)
        self.reset_annotations()

        state = self.document_state.get(document.file.get_uri()) or {}
        page = state.get("page")
        zoom = state.get("zoom")

        if (
            type(page) is int
            and 0 <= page < document.page_count
            and type(zoom) in (int, float)
            and 0.25 <= zoom <= 4.0
        ):
            self.viewer.set_zoom(zoom)
            self.viewer.go_to_page(page)
        else:
            self.apply_default_view()

        self.update_thumbnails(document)

        self.zoom_out_action.set_enabled(self.viewer.zoom > 0.25)
        self.zoom_in_action.set_enabled(self.viewer.zoom < 4.0)

        self.fit_width_action.set_enabled(
            True
        )

        self.fit_page_action.set_enabled(
            True
        )

        self.set_title(
            f"{document.name} — inPeDF"
        )


    def apply_default_view(self):
        """Apply the default document view preferences."""

        view_mode = self.settings.get_string(
            "default-view-mode"
        )

        if view_mode == "fit-width":
            self.viewer.fit_width()
            return

        if view_mode == "fit-page":
            self.viewer.fit_page()
            return

        zoom = self.settings.get_int(
            "default-zoom"
        )

        self.viewer.set_zoom(
            zoom / 100.0
        )
