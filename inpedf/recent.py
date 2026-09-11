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

"""Manage recently opened documents."""

import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gio, Gtk


MAX_RECENT_FILES = 10


class RecentFiles:
    """Manage recently opened PDF documents."""

    def __init__(self):
        self.manager = Gtk.RecentManager.get_default()

    def add(self, file):
        """Add a file to the recent documents list."""

        if not isinstance(file, Gio.File):
            file = Gio.File.new_for_path(
                str(file)
            )

        return self.manager.add_item(
            file.get_uri()
        )

    def get_items(self, limit=MAX_RECENT_FILES):
        """Return recently opened local PDF documents."""

        recent_items = []

        for info in self.manager.get_items():
            if info.get_mime_type() != "application/pdf":
                continue

            if not info.is_local():
                continue

            if not info.exists():
                continue

            if info.get_private_hint():
                continue

            modified = info.get_modified()

            recent_items.append(
                {
                    "name": info.get_display_name(),
                    "uri": info.get_uri(),
                    "modified": modified.to_unix(),
                }
            )

        recent_items.sort(
            key=lambda item: item["modified"],
            reverse=True,
        )

        return recent_items[:limit]