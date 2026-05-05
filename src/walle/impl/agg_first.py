from __future__ import annotations

from typing import Any

from ..agg import AggregateExpr
from ..util import Row
from .expr import Expr


class FirstExpr(AggregateExpr):
    def __init__(self, child: Expr) -> None:
        self._expr = child
        self._val: Any = None
        self._set: bool = False

    def reset(self) -> None:
        self._val = None
        self._set = False

    def push(self, point: Row) -> None:
        if self._set:
            return
        v = self._expr.eval(point)
        if v is None:
            return
        self._val = v
        self._set = True

    def pop(self, point: Row) -> None:
        raise NotImplementedError(
            "FirstExpr.pop() is not supported for sliding-window use"
        )

    def value(self) -> Any:
        return self._val
