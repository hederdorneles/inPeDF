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

"""Application settings support."""

from pathlib import Path

from gi.repository import Gio


SCHEMA_ID = "br.com.inpedf.InPeDF"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_SCHEMA_DIR = PROJECT_ROOT / "data"


def create_settings():
    """Create the application GSettings instance."""

    compiled_schema = (
        LOCAL_SCHEMA_DIR
        / "gschemas.compiled"
    )

    if compiled_schema.exists():
        default_source = (
            Gio.SettingsSchemaSource.get_default()
        )

        schema_source = (
            Gio.SettingsSchemaSource.new_from_directory(
                str(LOCAL_SCHEMA_DIR),
                default_source,
                False,
            )
        )

        schema = schema_source.lookup(
            SCHEMA_ID,
            True,
        )

        if schema is None:
            raise RuntimeError(
                f"GSettings schema not found: {SCHEMA_ID}"
            )

        return Gio.Settings.new_full(
            schema,
            None,
            None,
        )

    return Gio.Settings.new(
        SCHEMA_ID
    )