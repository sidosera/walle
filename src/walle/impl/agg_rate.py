from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import TypeAlias

from ..agg import AggregateExpr
from ..util import Row, duration_micros
from .expr import Expr


_Sample: TypeAlias = tuple[datetime, float]
_EDGE_FACTOR = 1.1
_MICROS_PER_SECOND = 10**6


class RateExpr(AggregateExpr):
    def __init__(self, expr: Expr, key: Expr, window: timedelta) -> None:
        window_s = duration_micros(window) / _MICROS_PER_SECOND
        if window_s <= 0:
            raise ValueError(f"rate window must be positive number, got {window}")

        self._expr = expr
        self._key = key
        self._window = window
        self._window_s = window_s
        self._samples: deque[_Sample] = deque()
        self._end: datetime | None = None

    def reset(self) -> None:
        self._samples.clear()
        self._end = None

    def _time(self, row: Row) -> datetime | None:
        t = self._key.eval(row)
        if t is None:
            return None
        if not isinstance(t, datetime):
            raise TypeError(
                f"rate key must evaluate to datetime, got {type(t).__name__}"
            )
        return t

    def _sample(self, row: Row) -> _Sample | None:
        t = self._time(row)
        if t is None:
            return None
        x = self._expr.eval(row)
        if x is None:
            return None
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError(f"rate value must be numeric, got {type(x).__name__}")
        return t, float(x)

    def push(self, point: Row) -> None:
        t = self._time(point)
        if t is None:
            return
        if self._samples and t < self._samples[-1][0]:
            raise ValueError("rate input must be sorted by time")
        self._end = t

        x = self._expr.eval(point)
        if x is not None:
            if isinstance(x, bool) or not isinstance(x, (int, float)):
                raise TypeError(f"rate value must be numeric, got {type(x).__name__}")
            self._samples.append((t, float(x)))

    def pop(self, point: Row) -> None:
        if self._sample(point) is not None and self._samples:
            self._samples.popleft()

    def value(self) -> float | None:
        samples = self._samples
        n = len(samples)
        if n < 2 or self._end is None:
            return None

        start = self._end - self._window

        t0, x0 = samples[0]
        t1, x1 = samples[-1]

        span = duration_micros(t1 - t0) / _MICROS_PER_SECOND
        if span <= 0:
            return None

        inc = x1 - x0
        prev = x0
        it = iter(samples)
        next(it)
        for _, x in it:
            if x < prev:
                inc += prev
            prev = x

        step = span / (n - 1)
        limit = _EDGE_FACTOR * step

        pre_gap = duration_micros(t0 - start) / _MICROS_PER_SECOND
        pre = step / 2 if pre_gap >= limit else pre_gap
        if inc > 0 and x0 >= 0:
            zero = span * x0 / inc
            pre = min(pre, zero)

        post_gap = duration_micros(self._end - t1) / _MICROS_PER_SECOND
        post = step / 2 if post_gap >= limit else post_gap

        increase = inc * (span + pre + post) / span
        return increase / self._window_s
