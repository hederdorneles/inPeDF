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

from gi.repository import Adw, Gio, GLib, Gtk

from .i18n import _
from .widgets.viewer import PDFViewer


class MainWindow(Adw.ApplicationWindow):
    """Janela principal do leitor de PDF."""


    def __init__(self, application):
        super().__init__(application=application)

        self.settings = application.settings

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

        self.build_ui()

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


    def on_close_request(self, window):
        """Save the window state before closing."""

        self.save_window_state()

        return False


    def build_ui(self):
        """Constrói a interface principal."""
        self.toolbar_view = Adw.ToolbarView()

        self.set_content(
            self.toolbar_view
        )

        self.create_header_bar()
        self.create_content()
        self.create_bottom_bar()


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

        pages = self.create_sidebar_placeholder(
            _("Page thumbnails")
        )

        outline = self.create_sidebar_placeholder(
            _("Document outline")
        )

        annotations = self.create_sidebar_placeholder(
            _("Annotations")
        )

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

        self.viewer.set_document(
            document
        )

        self.zoom_out_action.set_enabled(
            True
        )

        self.zoom_in_action.set_enabled(
            True
        )

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
