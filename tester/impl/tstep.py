from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from ..util import Row, duration_micros
from .expr import Expr


class TStep(Expr):
    def __init__(self, size: timedelta, start: datetime, child: Expr) -> None:
        self._size = size
        self._start = start
        self._child = child

    def eval(self, row: Row) -> Any:
        t = self._child.eval(row)
        elapsed = duration_micros(t - self._start)
        step_size = duration_micros(self._size)
        quotient, remainder = divmod(elapsed, step_size)
        n = max(1, quotient) if remainder == 0 else quotient + 1
        return self._start + timedelta(microseconds=n * step_size)
