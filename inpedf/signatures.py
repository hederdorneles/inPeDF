"""Read-only signature details and asynchronous local cryptographic checks.

Copyright (C) 2026 Heder Dorneles Soares
License: GPL-2.0-only
"""

from gi.repository import Adw, Gio, GLib, Gtk, Poppler

from .i18n import _


def signature_locations(document):
    locations = {}
    for number in range(document.get_n_pages()):
        for mapping in document.get_page(number).get_form_field_mapping():
            if mapping.field.get_field_type() == Poppler.FormFieldType.SIGNATURE:
                locations[mapping.field.get_id()] = number
    return locations


def signature_status(status):
    return {
        Poppler.SignatureStatus.VALID: _("Valid for the signed revision"),
        Poppler.SignatureStatus.INVALID: _("Invalid signature"),
        Poppler.SignatureStatus.DIGEST_MISMATCH: _("The signed content does not match the signature"),
        Poppler.SignatureStatus.DECODING_ERROR: _("Unable to decode the signature"),
        Poppler.SignatureStatus.GENERIC_ERROR: _("Unable to check the signature"),
        Poppler.SignatureStatus.NOT_FOUND: _("No signature data found"),
        Poppler.SignatureStatus.NOT_VERIFIED: _("Not checked"),
    }.get(status, _("Unknown status"))


class SignaturesDialog(Adw.Dialog):
    def __init__(self, window, selected_id=None):
        super().__init__(title=_("Digital signatures"), content_width=640, content_height=620)
        self.window = window
        self.document = window.viewer.document.document
        self.cancellable = Gio.Cancellable()
        self.closed = False
        self.status_rows = {}
        self.connect("closed", self.on_closed)

        toolbar = Adw.ToolbarView()
        toolbar.add_top_bar(Adw.HeaderBar())
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16,
                          margin_top=18, margin_bottom=18, margin_start=18, margin_end=18)
        notice = Gtk.Label(
            label=_("Local cryptographic check. Certificate trust, revocation and later document revisions are not assessed."),
            wrap=True, xalign=0,
        )
        content.append(notice)
        locations = signature_locations(self.document)
        fields = list(self.document.get_signature_fields())
        if selected_id is not None:
            fields.sort(key=lambda field: field.get_id() != selected_id)
        if not fields:
            content.append(Gtk.Label(label=_("This PDF has no digital signatures"), wrap=True))

        for field in fields:
            group = Adw.PreferencesGroup(title=field.get_name() or _("Digital signature"))
            content.append(group)
            rows = {}
            for key, title in (
                ("signer", _("Signer")),
                ("time", _("Declared signing time")),
                ("issuer", _("Certificate issuer")),
                ("valid_from", _("Certificate valid from")),
                ("valid_until", _("Certificate valid until")),
                ("status", _("Cryptographic signature")),
            ):
                row = Adw.ActionRow(title=title, use_markup=False)
                row.set_subtitle(_("Checking…"))
                row.set_subtitle_selectable(True)
                group.add(row)
                rows[key] = row
            self.status_rows[field.get_id()] = rows
            page = locations.get(field.get_id())
            if page is not None:
                button = Gtk.Button(label=_("Go to page {number}").format(number=page + 1))
                button.connect("clicked", self.on_go_to_page, page)
                group.add(button)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(content)
        toolbar.set_content(scrolled)
        self.set_child(toolbar)
        self.pending_fields = iter(fields)
        self.check_next_signature()

    def check_next_signature(self):
        if self.closed:
            return
        field = next(self.pending_fields, None)
        if field is not None:
            # Verify one field at a time: the NSS backend shares document state.
            # Zero flags avoids certificate validation and online requests.
            field.signature_validate_async(
                Poppler.SignatureValidationFlags(0), self.cancellable,
                self.on_signature_checked,
            )

    def on_signature_checked(self, field, result):
        try:
            info = field.signature_validate_finish(result)
        except GLib.Error as error:
            if not self.closed:
                rows = self.status_rows[field.get_id()]
                for row in rows.values():
                    row.set_subtitle(_("Unavailable"))
                rows["status"].set_subtitle(str(error))
                self.check_next_signature()
            return
        if self.closed:
            return
        certificate = info.get_certificate_info()
        values = {
            "signer": info.get_signer_name(),
            "time": self.format_time(info.get_local_signing_time()),
            "issuer": certificate.get_issuer_common_name() if certificate else None,
            "valid_from": self.format_time(certificate.get_issuance_time()) if certificate else None,
            "valid_until": self.format_time(certificate.get_expiration_time()) if certificate else None,
            "status": signature_status(info.get_signature_status()),
        }
        for key, value in values.items():
            self.status_rows[field.get_id()][key].set_subtitle(value or _("Not specified"))
        self.check_next_signature()

    @staticmethod
    def format_time(value):
        return value.format("%Y-%m-%d %H:%M:%S %z") if value else None

    def on_go_to_page(self, button, page):
        # The dialog holds the original PDF even if an external open request arrives.
        if self.window.viewer.document.document is self.document:
            self.window.viewer.navigate_to_page(page)
        self.close()

    def on_closed(self, dialog):
        self.closed = True
        self.cancellable.cancel()
