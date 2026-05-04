from __future__ import annotations

from datetime import timedelta

from ..agg import Agg
from ..util import Row, duration_micros
from .agg_increase import IncreaseAgg
from .expr import Expr


class RateAgg(Agg):
    _MICROS_PER_SECOND = 1_000_000

    def __init__(self, expr: Expr, key: Expr, window: timedelta) -> None:
        self._increase = IncreaseAgg(expr, key, window)
        self._range_seconds = duration_micros(window) / self._MICROS_PER_SECOND
        if self._range_seconds <= 0:
            raise ValueError("window must be positive")

    def reset(self) -> None:
        self._increase.reset()

    def push(self, point: Row) -> None:
        self._increase.push(point)

    def pop(self, point: Row) -> None:
        self._increase.pop(point)

    def value(self) -> float | None:
        increase = self._increase.value()
        if increase is None:
            return None
        return increase / self._range_seconds
