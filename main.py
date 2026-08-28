#!/usr/bin/env python3
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

"""Ponto de entrada da aplicação inPeDF."""

import sys

from inpedf.application import InPeDFApplication


def main() -> int:
    """Inicializa e executa a aplicação."""
    app = InPeDFApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
