from __future__ import annotations

from typing import Any

from ..agg import AggregateExpr
from ..util import Row
from .expr import Expr


class LastExpr(AggregateExpr):
    def __init__(self, child: Expr) -> None:
        self._expr = child
        self._val: Any = None

    def reset(self) -> None:
        self._val = None

    def push(self, point: Row) -> None:
        self._val = self._expr.eval(point)

    def pop(self, point: Row) -> None:
        raise NotImplementedError(
            "LastExpr.pop() is not supported for sliding-window use"
        )

    def value(self) -> Any:
        return self._val
