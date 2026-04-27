# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path
from typing import TextIO

from ..operator import Operator
from ..util import Row, read_header


class Scan(Operator[Row]):
    def __init__(self, path: Path) -> None:
        self.path = path
        self._handle: TextIO | None = None
        self._reader: Iterator[list[str]] | None = None
        self._columns: list[str] = []
        self._line_number = 0

    def open(self) -> None:
        self._handle = self.path.open(encoding="utf-8", newline="")
        self._reader = csv.reader(self._handle)
        raw_header = read_header(self._reader, self.path)
        self._columns = [col.split(":")[0] for col in raw_header]
        self._line_number = 1

    def next(self) -> Row | None:
        if self._reader is None:
            return None

        try:
            row = next(self._reader)
        except StopIteration:
            return None

        self._line_number += 1
        if len(row) < len(self._columns):
            raise ValueError(
                f"csv row {self._line_number} has {len(row)} columns, expected {len(self._columns)}"
            )

        return dict(zip(self._columns, row))

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        self._reader = None
        self._columns = []
