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

from gi.repository import Adw, Gio, Gtk

from .i18n import _
from .widgets.viewer import PDFViewer


class MainWindow(Adw.ApplicationWindow):
    """Janela principal do leitor de PDF."""

    def __init__(self, application):
        super().__init__(application=application)

        self.set_title("inPeDF")
        self.set_default_size(1100, 750)
        self.set_size_request(700, 450)

        self.create_actions()
        self.build_ui()

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

        zoom_in_button = Gtk.Button(
            icon_name="zoom-in-symbolic",
            tooltip_text=_("Zoom in"),
        )

        zoom_out_button.set_sensitive(False)
        zoom_in_button.set_sensitive(False)

        self.header_bar.pack_end(
            zoom_in_button
        )

        self.header_bar.pack_end(
            zoom_out_button
        )

        menu_button = Gtk.MenuButton(
            icon_name="open-menu-symbolic",
            tooltip_text=_("Main menu"),
        )

        menu_button.set_menu_model(
            self.create_menu()
        )

        self.header_bar.pack_end(
            menu_button
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

    def on_previous_page(self, action, parameter):
        """Go to the previous page."""
        
        self.viewer.previous_page()

    def on_next_page(self, action, parameter):
        """Go to the next page."""

        self.viewer.next_page()

    def on_page_changed(self, viewer, page_number):
        """Update page information and navigation actions."""

        if viewer.document is None:
            return

        total_pages = viewer.document.page_count
        current_page = page_number + 1

        self.page_label.set_text(
            _("Page {current} of {total}").format(
                current=current_page,
                total=total_pages,
            )
        )

        self.previous_page_action.set_enabled(
            page_number > 0
        )

        self.next_page_action.set_enabled(
            page_number < total_pages - 1
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
        """Cria a barra inferior."""
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

        self.page_label = Gtk.Label(
            label=_("Page — / —")
        )

        bar.pack_start(
            previous_button
        )

        bar.pack_start(
            next_button
        )

        bar.pack_start(
            self.page_label
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

    def create_menu(self):
        """Cria o menu principal."""
        menu = Gio.Menu()

        file_section = Gio.Menu()

        file_section.append(
            _("Open…"),
            "app.open",
        )

        menu.append_section(
            None,
            file_section,
        )

        application_section = Gio.Menu()

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

    def on_sidebar_toggled(self, button):
        """Mostra ou oculta a barra lateral."""
        self.sidebar.set_visible(
            button.get_active()
        )

    def load_document(self, document):
        """Display a PDF document in the window."""

        self.viewer.set_document(
            document
        )

        self.set_title(
            f"{document.name} — inPeDF"
        )
