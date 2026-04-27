from __future__ import annotations

from ..operator import Operator, pull
from ..util import Row
from .expr import Expr


class Sort(Operator[Row]):
    def __init__(self, child: Operator[Row], key: Expr) -> None:
        super().__init__(child)
        self._key = key
        self._rows: list[Row] = []
        self._index = 0

    def open(self) -> None:
        super().open()
        self._rows = sorted(pull(self.child), key=lambda r: self._key.eval(r))
        self._index = 0

    def next(self) -> Row | None:
        if self._index >= len(self._rows):
            return None
        row = self._rows[self._index]
        self._index += 1
        return row

    def close(self) -> None:
        self._rows.clear()
        self._index = 0
        super().close()
