from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import TypeAlias

from ..agg import Agg
from ..util import Row, duration_micros
from .expr import Expr


_Sample: TypeAlias = tuple[datetime, float]

_EDGE_FACTOR = 1.1
_MICROS_PER_SECOND = 10**6


# Counter increase over a window W = [a, b].
#
# Let S = ((t_0, x_0), ..., (t_m, x_m)), m >= 1, be the non-null
# counter samples in W, ordered by time.
#
# span = t_m - t_0
# step = span / m
#
# inc = x_m - x_0 + sum(r_i for i = 1..m)
#
# r_i = x_{i-1}, if x_i < x_{i-1}
#     = 0,       otherwise
#
# e(g) = g,        if g < 1.1 * step
#      = step / 2, otherwise
#
# pre  = e(t_0 - a)
# post = e(b - t_m)
#
# If inc > 0 and x_0 >= 0:
#
#   pre = min(pre, span * x_0 / inc)
#
# increase = inc * (span + pre + post) / span

class IncreaseAgg(Agg):
    def __init__(self, expr: Expr, key: Expr, window: timedelta) -> None:
        window_s = duration_micros(window) / _MICROS_PER_SECOND
        assert window_s > 0

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

        assert isinstance(t, datetime)
        return t

    def _sample(self, row: Row) -> _Sample | None:
        t = self._time(row)
        if t is None:
            return None

        x = self._expr.eval(row)
        if x is None:
            return None

        assert isinstance(x, (int, float))
        return t, float(x)

    def push(self, point: Row) -> None:
        t = self._time(point)
        if t is None:
            return

        if self._samples and t < self._samples[-1][0]:
            raise ValueError("increase input must be sorted by time")

        self._end = t

        x = self._expr.eval(point)
        if x is not None:
            assert isinstance(x, (int, float))
            self._samples.append((t, float(x)))

    def pop(self, point: Row) -> None:
        if self._sample(point) is not None and self._samples:
            self._samples.popleft()

    def _increase(self) -> float | None:
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

        # inc = x_m - x_0 + sum(r_i for i = 1..m),
        # where r_i = x_{i-1} if x_i < x_{i-1}, else 0.
        inc = x1 - x0
        prev = x0

        it = iter(samples)
        next(it)

        for _, x in it:
            if x < prev:
                inc += prev
            prev = x

        # step = span / m, where m = number of adjacent sample intervals.
        step = span / (n - 1)
        limit = _EDGE_FACTOR * step

        # pre = e(t_0 - a), where:
        #
        # e(g) = g,        if g < 1.1 * step
        #      = step / 2, otherwise
        pre_gap = duration_micros(t0 - start) / _MICROS_PER_SECOND
        pre = step / 2 if pre_gap >= limit else pre_gap

        # pre = min(pre, zero), where zero = span * x_0 / inc.
        if inc > 0 and x0 >= 0:
            zero = span * x0 / inc
            pre = min(pre, zero)

        # post = e(b - t_m), with the same e(g).
        post_gap = duration_micros(self._end - t1) / _MICROS_PER_SECOND
        post = step / 2 if post_gap >= limit else post_gap

        # increase = inc * (span + pre + post) / span.
        return inc * (span + pre + post) / span

    def value(self) -> float | None:
        return self._increase()
