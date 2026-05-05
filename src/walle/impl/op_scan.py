from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import TextIO

from ..operator import Operator
from ..util import Row, read_header


class CsvScan(Operator[Row]):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path.expanduser()
        if not self._path.exists():
            raise FileNotFoundError(self._path)
        self._fd: TextIO | None = None
        self._reader: Iterator[list[str]] | None = None
        self._columns: list[str] = []
        self._line_number = 0

    def open(self) -> None:
        super().open()
        self._fd = self._path.open(encoding="utf-8", newline="")
        self._reader = csv.reader(self._fd)
        raw_header = read_header(self._reader, self._path)
        self._columns = [col.split(":")[0] for col in raw_header]
        self._line_number = 1

    def next(self) -> Row | None:
        if self._reader is None:
            raise RuntimeError("CsvScan.next() called before open()")
        try:
            row = next(self._reader)
        except StopIteration:
            return None
        self._line_number += 1

        if len(row) < len(self._columns):
            raise ValueError(
                f"line:{self._line_number} missing column, expected {len(self._columns)}, got {len(row)}"
            )

        return dict(zip(self._columns, row))

    def close(self) -> None:
        if self._fd is not None:
            self._fd.close()
        self._fd = None
        self._reader = None
        self._columns = []
        super().close()


class ListScan(Operator[Row]):
    def __init__(self, rows: Sequence[Row] | Iterable[Row]) -> None:
        super().__init__()
        self._rows: Sequence[Row] | Iterable[Row] = rows
        self._it: Iterator[Row] | None = None

    def open(self) -> None:
        super().open()
        self._it = iter(self._rows)

    def next(self) -> Row | None:
        if self._it is None:
            raise RuntimeError("ListScan.next() called before open()")
        row = next(self._it, None)
        if row is None:
            return None
        if not isinstance(row, dict):
            raise TypeError(f"ListScan expected row dict, got {type(row).__name__}")
        return dict(row)

    def close(self) -> None:
        self._it = None
        super().close()
