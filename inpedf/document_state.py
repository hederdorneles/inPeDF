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

        state = self.get(uri) or {}
        state.update({
            "page": int(page_number),
            "zoom": float(zoom),
            "updated": int(time.time()),
        })
        self.data[uri] = state

        self._prune()
        self._save()

    def get_bookmarks(self, uri):
        """Return page-number bookmarks, ignoring malformed legacy values."""
        state = self.get(uri) or {}
        bookmarks = state.get("bookmarks", {})
        if not isinstance(bookmarks, dict):
            return {}
        result = {}
        for key, title in bookmarks.items():
            try:
                page = int(key)
            except (TypeError, ValueError):
                continue
            if page >= 0 and isinstance(title, str):
                result[page] = title
        return dict(sorted(result.items()))

    def set_bookmark(self, uri, page, title):
        """Add or remove a bookmark and preserve the reading state."""
        previous = self.get(uri)
        state = (previous or {}).copy()
        bookmarks = self.get_bookmarks(uri)
        if title is None:
            bookmarks.pop(page, None)
        else:
            bookmarks[page] = title
        state["bookmarks"] = {str(number): text for number, text in bookmarks.items()}
        state["updated"] = int(time.time())
        self.data[uri] = state
        try:
            self._save()
        except OSError:
            if previous is None:
                self.data.pop(uri, None)
            else:
                self.data[uri] = previous
            raise

    def _prune(self):
        """Limit recent reading states while retaining personal bookmarks."""
        bookmarked = {
            uri: state for uri, state in self.data.items()
            if isinstance(state, dict) and self.get_bookmarks(uri)
        }
        recent = [
            (uri, state) for uri, state in self.data.items()
            if uri not in bookmarked and isinstance(state, dict)
        ]
        recent.sort(
            key=lambda item: (
                item[1].get("updated", 0)
                if isinstance(item[1].get("updated", 0), (int, float)) else 0
            ),
            reverse=True,
        )
        self.data = {**bookmarked, **dict(recent[:MAX_DOCUMENT_STATES])}
