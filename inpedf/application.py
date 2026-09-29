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

"""Classe principal da aplicação inPeDF."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk
from pathlib import Path
from .pdf.document import PDFDocument

from . import __version__
from .i18n import _
from .window import MainWindow

from .recent import RecentFiles

from .preferences import PreferencesDialog
from .settings import create_settings


APP_ID = "br.com.inpedf.InPeDF"


class InPeDFApplication(Adw.Application):
    """inPeDF Main application."""

    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

        self.window = None
        self.document = PDFDocument()
        self.recent_files = RecentFiles()
        self.settings = create_settings()

    def configure_icons(self):
        """Adiciona os ícones do inPeDF ao tema de ícones do GTK."""

        icons_path = (
            Path(__file__).resolve().parent
            / "resources"
            / "icons"
        )

        icon_theme = Gtk.IconTheme.get_for_display(
            self.window.get_display()
        )

        icon_theme.add_search_path(
            str(icons_path)
        )
    
    def do_startup(self):
        """Inicializa as ações da aplicação."""
        Adw.Application.do_startup(self)

        self.apply_color_scheme()

        self.settings.connect(
            "changed::color-scheme",
            self.on_color_scheme_changed,
        )

        self.create_action(
            "open",
            self.on_open,
            ["<Ctrl>O"],
        )

        open_recent_action = Gio.SimpleAction.new(
            "open-recent",
            GLib.VariantType.new("s"),
        )

        open_recent_action.connect(
            "activate",
            self.on_open_recent,
        )

        self.add_action(
            open_recent_action
        )

        self.create_action(
            "preferences",
            self.on_preferences,
        )

        self.create_action(
            "about",
            self.on_about,
        )

        self.create_action(
            "quit",
            self.on_quit,
            ["<Ctrl>Q"],
        )

    def do_activate(self):
        """Cria ou apresenta a janela principal."""
        if self.window is None:
            self.window = MainWindow(self)
            self.configure_icons()

        self.window.present()

    def create_action(self, name, callback, shortcuts=None):
        """Cria uma ação global da aplicação."""
        action = Gio.SimpleAction.new(name, None)

        action.connect(
            "activate",
            callback,
        )

        self.add_action(action)

        if shortcuts:
            self.set_accels_for_action(
                f"app.{name}",
                shortcuts,
            )

    def on_open(self, action, parameter):
        """Open the PDF documents selector."""
        dialog = Gtk.FileDialog()

        dialog.set_title(
            _("Open PDF")
        )

        pdf_filter = Gtk.FileFilter()

        pdf_filter.set_name(
            _("PDF documents")
        )

        pdf_filter.add_mime_type(
            "application/pdf"
        )

        pdf_filter.add_pattern(
            "*.pdf"
        )

        filters = Gio.ListStore.new(
            Gtk.FileFilter
        )

        filters.append(
            pdf_filter
        )

        dialog.set_filters(
            filters
        )

        dialog.set_default_filter(
            pdf_filter
        )

        dialog.open(
            self.window,
            None,
            self.on_open_finish,
        )

    def on_open_recent(self, action, parameter):
        """Open a document from the recent files list."""

        if parameter is None:
            return

        uri = parameter.get_string()

        file = Gio.File.new_for_uri(
            uri
        )

        try:
            self.document.open(
                file
            )

            self.window.load_document(
                self.document
            )

            self.recent_files.add(
                file
            )

        except GLib.Error as error:
            self.show_error(
                _("Unable to open PDF"),
                str(error),
            )

    def on_open_recent(self, action, parameter):
        """Open a document from the recent files list."""

        if parameter is None:
            return

        uri = parameter.get_string()

        file = Gio.File.new_for_uri(
            uri
        )

        try:
            self.document.open(
                file
            )

            self.window.load_document(
                self.document
            )

            self.recent_files.add(
                file
            )

        except GLib.Error as error:
            self.show_error(
                _("Unable to open PDF"),
                str(error),
            )

    def on_open_finish(self, dialog, result):
        """Processa o arquivo escolhido pelo usuário."""

        try:
            file = dialog.open_finish(
                result
            )

        except GLib.Error:
            # Normalmente significa que o usuário
            # cancelou o seletor de arquivos.
            return

        try:
            self.document.open(
                file
            )

            self.window.load_document(
                self.document
            )

            self.recent_files.add(
                file
            )

            self.window.refresh_menu()

        except GLib.Error as error:
            self.show_error(
                _("Unable to open PDF"),
                str(error),
            )

    def show_error(self, heading, message):
        """Exibe uma mensagem de erro"""
        dialog = Adw.AlertDialog.new(
            heading,
            message,
        )

        dialog.add_response(
            "ok",
            _("OK"),
        )

        dialog.set_default_response(
            "ok"
        )

        dialog.set_close_response(
            "ok"
        )

        dialog.present(
            self.window
        )


    def apply_color_scheme(self):
        """Apply the configured application color scheme."""

        style_manager = (
            Adw.StyleManager.get_default()
        )

        color_scheme = self.settings.get_string(
            "color-scheme"
        )

        schemes = {
            "system": Adw.ColorScheme.PREFER_LIGHT,
            "light": Adw.ColorScheme.FORCE_LIGHT,
            "dark": Adw.ColorScheme.FORCE_DARK,
        }

        style_manager.set_color_scheme(
            schemes.get(
                color_scheme,
                Adw.ColorScheme.PREFER_LIGHT,
            )
        )


    def on_color_scheme_changed(self, settings, key):
        """Apply color scheme changes immediately."""

        self.apply_color_scheme()


    def on_preferences(self, action, parameter):
        """Show the application preferences."""

        dialog = PreferencesDialog(
            self.settings
        )

        dialog.present(
            self.window
        )


    def on_about(self, action, parameter):
        """Exibe informações sobre o inPeDF."""
        about = Adw.AboutDialog()

        about.set_application_name("inPeDF")
        about.set_application_icon("inpedf")

        about.set_developer_name(
            "Heder Dorneles Soares"
        )

        about.set_version(__version__)

        about.set_comments(
            _(
                "A PDF document reader designed for "
                "the GNOME desktop."
            )
        )

        about.set_copyright(
            "Copyright © 2026 Heder Dorneles Soares"
        )

        about.set_license_type(
            Gtk.License.GPL_2_0_ONLY
        )

        about.set_developers(
            [
                "Heder Dorneles Soares "
                "<heder.soares@inpe.br>"
            ]
        )

        about.present(self.window)

    def on_quit(self, action, parameter):
        """Encerra a aplicação."""
        self.quit()
