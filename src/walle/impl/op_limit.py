from __future__ import annotations

from ..operator import Operator
from ..util import Row


class Limit(Operator[Row]):
    def __init__(self, child: Operator[Row], count: int, offset: int = 0) -> None:
        super().__init__(child)
        if count < 0:
            raise ValueError(f"limit count must be >= 0, got {count}")
        if offset < 0:
            raise ValueError(f"limit offset must be >= 0, got {offset}")
        self._count = count
        self._offset = offset
        self._emitted = 0
        self._skipped = 0

    def open(self) -> None:
        super().open()
        self._emitted = 0
        self._skipped = 0

    def next(self) -> Row | None:
        if self.child is None:
            raise RuntimeError("Limit requires a child operator")
        while self._skipped < self._offset:
            row = self.child.next()
            if row is None:
                return None
            if not isinstance(row, dict):
                raise TypeError(f"Limit expected row dict, got {type(row).__name__}")
            self._skipped += 1

        if self._emitted >= self._count:
            return None

        row = self.child.next()
        if row is None:
            return None
        if not isinstance(row, dict):
            raise TypeError(f"Limit expected row dict, got {type(row).__name__}")
        self._emitted += 1
        return row

    def close(self) -> None:
        self._emitted = 0
        self._skipped = 0
        super().close()
