from __future__ import annotations

from ..agg import Agg
from ..util import Row
from .expr import Expr


class SumAgg(Agg):
    def __init__(self, expr: Expr) -> None:
        self._expr = expr
        self._total: int = 0

    def reset(self) -> None:
        self._total = 0

    def push(self, point: Row) -> None:
        self._total += self._expr.eval(point)

    def pop(self, point: Row) -> None:
        self._total -= self._expr.eval(point)

    def value(self) -> int:
        return self._total
