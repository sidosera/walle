from __future__ import annotations

from collections import deque
from typing import Any

from ..agg import AggregateExpr
from ..util import Row
from .expr import Expr


class MaxExpr(AggregateExpr):
    def __init__(self, expr: Expr) -> None:
        self._expr = expr
        self._q: deque[Any] = deque()

    def reset(self) -> None:
        self._q.clear()

    def push(self, point: Row) -> None:
        v = self._expr.eval(point)
        if v is None:
            return
        while self._q and self._q[-1] <= v:
            self._q.pop()
        self._q.append(v)

    def pop(self, point: Row) -> None:
        v = self._expr.eval(point)
        if v is None:
            return
        if not self._q:
            raise RuntimeError("MaxExpr.pop() called on empty state")
        if self._q and self._q[0] == v:
            self._q.popleft()

    def value(self) -> Any:
        if not self._q:
            return None
        return self._q[0]
