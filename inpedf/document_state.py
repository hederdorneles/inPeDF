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

"""Store per-document reading state."""

import json
import time
from pathlib import Path

from gi.repository import GLib


MAX_DOCUMENT_STATES = 100


class DocumentStateStore:
    """Store and restore per-document reading state."""

    def __init__(self):
        self.state_dir = (
            Path(GLib.get_user_state_dir())
            / "inpedf"
        )

        self.state_file = (
            self.state_dir
            / "documents.json"
        )

        self.state_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.data = self._load()

    def _load(self):
        """Load document state from disk."""

        if not self.state_file.exists():
            return {}

        try:
            with self.state_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

        if not isinstance(data, dict):
            return {}

        return data

    def _save(self):
        """Write document state to disk."""

        temporary_file = self.state_file.with_suffix(
            ".tmp"
        )

        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                self.data,
                file,
                indent=2,
                ensure_ascii=False,
            )

        temporary_file.replace(
            self.state_file
        )

    def get(self, uri):
        """Return saved state for a document."""

        state = self.data.get(uri)

        if not isinstance(state, dict):
            return None

        return state.copy()

    def set(self, uri, page_number, zoom):
        """Store reading state for a document."""

        self.data[uri] = {
            "page": int(page_number),
            "zoom": float(zoom),
            "updated": int(time.time()),
        }

        self._prune()
        self._save()

    def _prune(self):
        """Keep only the most recently updated document states."""

        if len(self.data) <= MAX_DOCUMENT_STATES:
            return

        items = sorted(
            self.data.items(),
            key=lambda item: item[1].get(
                "updated",
                0,
            ),
            reverse=True,
        )

        self.data = dict(
            items[:MAX_DOCUMENT_STATES]
        )