from __future__ import annotations

from ..operator import Operator
from ..util import Row


class Limit(Operator[Row]):
    def __init__(self, child: Operator[Row], count: int, offset: int = 0) -> None:
        super().__init__(child)
        self._count = count
        self._offset = offset
        self._emitted = 0
        self._skipped = 0

    def open(self) -> None:
        super().open()
        self._emitted = 0
        self._skipped = 0

    def next(self) -> Row | None:
        while self._skipped < self._offset:
            row = self.child.next()
            if row is None:
                return None
            self._skipped += 1

        if self._emitted >= self._count:
            return None

        row = self.child.next()
        if row is None:
            return None
        self._emitted += 1
        return row

    def close(self) -> None:
        self._emitted = 0
        self._skipped = 0
        super().close()
