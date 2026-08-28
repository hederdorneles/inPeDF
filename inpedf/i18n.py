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

"""Suporte à internacionalização do inPeDF."""

import gettext
from pathlib import Path


TEXT_DOMAIN = "inpedf"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_LOCALE_DIR = PROJECT_ROOT / "locale"
SYSTEM_LOCALE_DIR = Path("/usr/share/locale")


def get_locale_dir():
    """Retorna o diretório que contém os catálogos de tradução."""
    if LOCAL_LOCALE_DIR.exists():
        return LOCAL_LOCALE_DIR

    return SYSTEM_LOCALE_DIR


_translation = gettext.translation(
    TEXT_DOMAIN,
    localedir=get_locale_dir(),
    fallback=True,
)

_ = _translation.gettext
ngettext = _translation.ngettext
