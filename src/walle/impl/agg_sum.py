from __future__ import annotations

from ..agg import AggregateExpr
from ..util import Row
from .expr import Expr


class SumExpr(AggregateExpr):
    def __init__(self, expr: Expr) -> None:
        self._expr = expr
        self._total: int = 0
        self._seen_value = False
        self._non_null_count = 0

    def reset(self) -> None:
        self._total = 0
        self._seen_value = False
        self._non_null_count = 0

    def push(self, point: Row) -> None:
        value = self._expr.eval(point)
        if value is None:
            return
        self._seen_value = True
        self._non_null_count += 1
        self._total += value

    def pop(self, point: Row) -> None:
        value = self._expr.eval(point)
        if value is None:
            return
        if self._non_null_count == 0:
            raise RuntimeError("SumExpr.pop() called without matching push()")
        self._non_null_count -= 1
        self._total -= value

    def value(self) -> int | None:
        if self._seen_value is False:
            return None
        return self._total
