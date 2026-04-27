from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import TextIO

from ..operator import Operator
from ..util import Row, read_header


class Scan(Operator[Row]):
    def __init__(self, source: Path | Sequence[Row] | Iterable[Row]) -> None:
        self._source = source
        self._handle: TextIO | None = None
        self._reader: Iterator[list[str]] | None = None
        self._rows: Iterator[Row] | None = None
        self._columns: list[str] = []
        self._line_number = 0

    def open(self) -> None:
        if isinstance(self._source, Path):
            self._handle = self._source.open(encoding="utf-8", newline="")
            self._reader = csv.reader(self._handle)
            raw_header = read_header(self._reader, self._source)
            self._columns = [col.split(":")[0] for col in raw_header]
            self._line_number = 1
            return
        self._rows = iter(self._source)

    def next(self) -> Row | None:
        if self._rows is not None:
            row = next(self._rows, None)
            if row is None:
                return None
            return dict(row)

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
        self._rows = None
        self._columns = []
