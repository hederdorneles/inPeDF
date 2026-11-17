"""Desktop controls for the shared streaming PDF exporter.

Copyright (C) 2026 Heder Dorneles Soares
License: GPL-2.0-only
"""

from pathlib import Path
import tempfile

from gi.repository import Adw, GLib, Gtk

from .export import FORMATS, page_indices, publish_outputs, write_document
from .i18n import _


class ExportDialog:
    def __init__(self, window):
        self.window = window
        self.document = window.viewer.document.document
        self.file = window.viewer.document.file
        self.current_page = window.viewer.page_number + 1
        self.source_id = 0
        self.iterator = None
        self.staging = None
        self.empty_pages = 0

    def present(self):
        dialog = Adw.AlertDialog.new(_("Export document"), _("Choose a format and page range."))
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        content.append(Gtk.Label(label=_("Format"), xalign=0))
        self.format = Gtk.DropDown.new_from_strings(["Markdown (.md)", "Text (.txt)", "JSON (.json)", _("All formats")])
        content.append(self.format)
        content.append(Gtk.Label(label=_("Pages: all, current, or 1,3-5"), xalign=0))
        self.pages = Gtk.Entry(text="all")
        content.append(self.pages)
        self.overwrite = Gtk.CheckButton(label=_("Replace existing files"))
        content.append(self.overwrite)
        dialog.set_extra_child(content)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("export", _("Choose output folder"))
        dialog.set_response_appearance("export", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("export")
        dialog.set_close_response("cancel")
        dialog.connect("response", self.on_options_response)
        dialog.present(self.window)

    def on_options_response(self, dialog, response):
        if response != "export":
            return
        self.page_spec = self.pages.get_text().strip()
        if self.page_spec == "current":
            self.page_spec = str(self.current_page)
        try:
            page_indices(self.page_spec, self.document.get_n_pages())
        except ValueError as error:
            self.window.get_application().show_error(_("Unable to export PDF"), str(error))
            return
        formats = FORMATS
        selected = self.format.get_selected()
        self.formats = list(formats) if selected == 3 else [formats[selected]]
        self.replace = self.overwrite.get_active()
        chooser = Gtk.FileDialog(title=_("Choose output folder"))
        chooser.select_folder(self.window, None, self.on_folder_selected)

    def on_folder_selected(self, chooser, result):
        try:
            folder = chooser.select_folder_finish(result)
            path = folder.get_path()
            if path is None:
                raise ValueError(_("Choose a local folder."))
            output_dir = Path(path)
            stem = Path(self.file.get_basename()).stem
            self.destinations = {fmt: output_dir / (stem + "." + fmt) for fmt in self.formats}
            if not self.replace and any(path.exists() for path in self.destinations.values()):
                raise FileExistsError(_("Output already exists. Enable Replace existing files to continue."))
            self.staging = tempfile.TemporaryDirectory(prefix=".inpedf-", dir=output_dir)
            self.iterator = write_document(
                self.document, self.file.get_uri(), self.formats, self.staging.name, self.page_spec
            )
        except GLib.Error as error:
            if not (error.matches(Gtk.DialogError.quark(), Gtk.DialogError.DISMISSED)
                    or error.matches(Gtk.DialogError.quark(), Gtk.DialogError.CANCELLED)):
                self.window.get_application().show_error(_("Unable to export PDF"), str(error))
            return
        except (OSError, ValueError) as error:
            self.cleanup()
            self.window.get_application().show_error(_("Unable to export PDF"), str(error))
            return

        self.progress = Adw.AlertDialog.new(_("Exporting document"), None)
        self.progress.set_body_use_markup(False)
        self.progress.add_response("cancel", _("Cancel"))
        self.progress.set_close_response("cancel")
        self.progress.connect("response", self.on_cancel)
        self.progress.present(self.window)
        self.source_id = GLib.idle_add(self.step)

    def step(self):
        try:
            current, total, number, has_text = next(self.iterator)
            self.empty_pages += not has_text
            self.progress.set_body(
                _("Exporting page {current} of {total}").format(current=current, total=total)
            )
            return GLib.SOURCE_CONTINUE
        except StopIteration:
            try:
                publish_outputs(self.staging.name, self.destinations, self.replace)
            except OSError as error:
                self.finish_error(error)
                return GLib.SOURCE_REMOVE
            self.source_id = 0
            self.cleanup()
            self.progress.close()
            message = "\n".join(str(path) for path in self.destinations.values())
            if self.empty_pages:
                message += "\n\n" + _("{count} pages have no extractable text. OCR may be required.").format(count=self.empty_pages)
            dialog = Adw.AlertDialog.new(_("Export complete"), message)
            dialog.set_body_use_markup(False)
            dialog.add_response("close", _("Close"))
            dialog.present(self.window)
            return GLib.SOURCE_REMOVE
        except Exception as error:
            self.finish_error(error)
            return GLib.SOURCE_REMOVE

    def finish_error(self, error):
        self.source_id = 0
        self.cleanup()
        self.progress.close()
        self.window.get_application().show_error(_("Unable to export PDF"), str(error))

    def on_cancel(self, dialog, response):
        if self.source_id:
            GLib.source_remove(self.source_id)
            self.source_id = 0
        self.cleanup()

    def cleanup(self):
        if self.iterator is not None:
            self.iterator.close()
            self.iterator = None
        if self.staging is not None:
            self.staging.cleanup()
            self.staging = None
