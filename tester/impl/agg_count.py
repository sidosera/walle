from __future__ import annotations

from ..agg import Agg
from ..util import Row
from .expr import Expr


class CountAgg(Agg):
    def __init__(self, expr: Expr | None = None) -> None:
        self._expr = expr
        self._count: int = 0

    def reset(self) -> None:
        self._count = 0

    def push(self, point: Row) -> None:
        if self._expr is not None and self._expr.eval(point) is None:
            return
        self._count += 1

    def pop(self, point: Row) -> None:
        if self._expr is not None and self._expr.eval(point) is None:
            return
        self._count -= 1

    def value(self) -> int:
        return self._count
