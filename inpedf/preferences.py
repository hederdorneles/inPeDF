# -*- coding: utf-8 -*-
#
# inPeDF - PDF document reader
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

"""Preferences dialog for inPeDF."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gtk

from .i18n import _


class PreferencesDialog(Adw.PreferencesDialog):
    """Application preferences dialog."""

    def __init__(self, settings):
        super().__init__()

        self.settings = settings

        self.set_title(
            _("Preferences")
        )

        self.create_interface()

    def create_interface(self):
        """Create the preferences interface."""

        page = Adw.PreferencesPage()

        page.set_title(
            _("General")
        )

        page.set_icon_name(
            "preferences-system-symbolic"
        )

        self.add(
            page
        )

        self.create_appearance_group(
            page
        )

        self.create_view_group(
            page
        )

    def create_appearance_group(self, page):
        """Create appearance preferences."""

        group = Adw.PreferencesGroup()

        group.set_title(
            _("Appearance")
        )

        page.add(
            group
        )

        self.theme_row = Adw.ComboRow()

        self.theme_row.set_title(
            _("Color scheme")
        )

        theme_model = Gtk.StringList.new(
            [
                _("System"),
                _("Light"),
                _("Dark"),
            ]
        )

        self.theme_row.set_model(
            theme_model
        )

        theme_values = {
            "system": 0,
            "light": 1,
            "dark": 2,
        }

        current_theme = self.settings.get_string(
            "color-scheme"
        )

        self.theme_row.set_selected(
            theme_values.get(
                current_theme,
                0,
            )
        )

        self.theme_row.connect(
            "notify::selected",
            self.on_theme_changed,
        )

        group.add(
            self.theme_row
        )

    def create_view_group(self, page):
        """Create document view preferences."""

        group = Adw.PreferencesGroup()

        group.set_title(
            _("Document view")
        )

        page.add(
            group
        )

        self.sidebar_row = Adw.SwitchRow()

        self.sidebar_row.set_title(
            _("Show sidebar")
        )

        self.sidebar_row.set_subtitle(
            _("Show the sidebar when the application starts")
        )

        self.sidebar_row.set_active(
            self.settings.get_boolean(
                "sidebar-visible"
            )
        )

        self.sidebar_row.connect(
            "notify::active",
            self.on_sidebar_changed,
        )

        group.add(
            self.sidebar_row
        )

        self.view_mode_row = Adw.ComboRow()

        self.view_mode_row.set_title(
            _("Default view mode")
        )

        view_model = Gtk.StringList.new(
            [
                _("Manual zoom"),
                _("Fit width"),
                _("Fit page"),
            ]
        )

        self.view_mode_row.set_model(
            view_model
        )

        view_values = {
            "manual": 0,
            "fit-width": 1,
            "fit-page": 2,
        }

        current_view = self.settings.get_string(
            "default-view-mode"
        )

        self.view_mode_row.set_selected(
            view_values.get(
                current_view,
                0,
            )
        )

        self.view_mode_row.connect(
            "notify::selected",
            self.on_view_mode_changed,
        )

        group.add(
            self.view_mode_row
        )

        self.zoom_row = Adw.SpinRow.new_with_range(
            25,
            400,
            25,
        )

        self.zoom_row.set_title(
            _("Default zoom")
        )

        self.zoom_row.set_subtitle(
            _("Used when manual zoom is selected")
        )

        self.zoom_row.set_numeric(
            True
        )

        self.zoom_row.set_value(
            self.settings.get_int(
                "default-zoom"
            )
        )

        self.zoom_row.connect(
            "notify::value",
            self.on_default_zoom_changed,
        )

        group.add(
            self.zoom_row
        )

        self.update_zoom_sensitivity()

    def on_theme_changed(self, row, parameter):
        """Store the selected color scheme."""

        values = [
            "system",
            "light",
            "dark",
        ]

        selected = row.get_selected()

        if selected >= len(values):
            return

        self.settings.set_string(
            "color-scheme",
            values[selected],
        )

    def on_sidebar_changed(self, row, parameter):
        """Store the sidebar visibility preference."""

        self.settings.set_boolean(
            "sidebar-visible",
            row.get_active(),
        )

    def on_view_mode_changed(self, row, parameter):
        """Store the default document view mode."""

        values = [
            "manual",
            "fit-width",
            "fit-page",
        ]

        selected = row.get_selected()

        if selected >= len(values):
            return

        self.settings.set_string(
            "default-view-mode",
            values[selected],
        )

        self.update_zoom_sensitivity()

    def on_default_zoom_changed(self, row, parameter):
        """Store the default manual zoom level."""

        self.settings.set_int(
            "default-zoom",
            int(row.get_value()),
        )

    def update_zoom_sensitivity(self):
        """Enable default zoom only for manual view mode."""

        manual_mode = (
            self.view_mode_row.get_selected() == 0
        )

        self.zoom_row.set_sensitive(
            manual_mode
        )