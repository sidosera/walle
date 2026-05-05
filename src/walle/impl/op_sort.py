from __future__ import annotations

from collections.abc import Sequence
from functools import cmp_to_key

from ..operator import Operator, pull
from ..util import Row
from .expr import Expr


class SortKey:
    def __init__(
        self, expr: Expr, *, descending: bool = False, nulls_first: bool = False
    ) -> None:
        self.expr = expr
        self.descending = descending
        self.nulls_first = nulls_first


class Sort(Operator[Row]):
    def __init__(self, child: Operator[Row], keys: Sequence[SortKey]) -> None:
        super().__init__(child)
        if not keys:
            raise ValueError("Sort requires at least one sort key")
        self._keys = tuple(keys)
        self._rows: list[Row] = []
        self._index = 0

    def open(self) -> None:
        super().open()
        if self.child is None:
            raise RuntimeError("Sort requires a child operator")
        self._rows = sorted(pull(self.child), key=cmp_to_key(self._compare_rows))
        self._index = 0

    def _compare_rows(self, left_row: Row, right_row: Row) -> int:
        if not isinstance(left_row, dict) or not isinstance(right_row, dict):
            raise TypeError("Sort rows must be dict objects")
        for key in self._keys:
            left = key.expr.eval(left_row)
            right = key.expr.eval(right_row)
            if left is None or right is None:
                if left is None and right is None:
                    continue
                if left is None:
                    return -1 if key.nulls_first else 1
                return 1 if key.nulls_first else -1
            if left == right:
                continue
            if left < right:
                return -1 if key.descending is False else 1
            return 1 if key.descending is False else -1
        return 0

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
