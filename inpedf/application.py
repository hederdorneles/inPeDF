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


APP_ID = "br.com.inpedf.InPeDF"


class InPeDFApplication(Adw.Application):
    """Aplicação principal do inPeDF."""

    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

        self.window = None
        self.document = PDFDocument()

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

        self.create_action(
            "open",
            self.on_open,
            ["<Ctrl>O"],
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
        """Abre o seletor de documentos PDF."""
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
