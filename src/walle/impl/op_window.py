from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import cast

from ..agg import _agg
from ..operator import Operator
from ..util import Row
from .op_eval import Map
from .expr import Expr


class WindowedAggregate(Operator[Row]):
    """Sliding-window aggregate operator.

    The operator manages membership of rows in the active time window and
    drives aggregate-function expressions (`AggregateExpr`) through `push`/`pop`.
    """

    def __init__(
        self,
        child: Operator[Row],
        window: timedelta,
        key: Expr,
        fn: Sequence[Map],
    ) -> None:
        super().__init__(child)
        if window <= timedelta(0):
            raise ValueError(f"window must be > 0, got {window}")
        self._window_size = window
        self._key = key
        self._fn: tuple[Map, ...] = tuple(fn)
        if not self._fn:
            raise ValueError(
                "WindowedAggregate requires at least one aggregate function"
            )
        self._window: deque[Row] = deque()
        self._last_time: datetime | None = None

    def open(self) -> None:
        super().open()
        if self.child is None:
            raise RuntimeError("WindowedAggregate requires a child operator")
        self._window.clear()
        self._last_time = None
        for ev in self._fn:
            _agg(ev).reset()

    def next(self) -> Row | None:
        while True:
            row = self.child.next()
            if row is None:
                return None
            if not isinstance(row, dict):
                raise TypeError(
                    f"WindowedAggregate expected row dict, got {type(row).__name__}"
                )

            t_value = self._key.eval(row)
            if not isinstance(t_value, datetime):
                raise TypeError(
                    f"window key must evaluate to datetime, got {type(t_value).__name__}"
                )
            t = cast(datetime, t_value)
            if self._last_time is not None and t < self._last_time:
                raise ValueError("window input must be sorted by time")
            self._last_time = t

            while (
                self._window
                and (old_time := self._key.eval(self._window[0])) is not None
                and isinstance(old_time, datetime)
                and old_time <= t - self._window_size
            ):
                evicted = self._window.popleft()
                for ev in self._fn:
                    _agg(ev).pop(evicted)
            if self._window:
                old_time = self._key.eval(self._window[0])
                if not isinstance(old_time, datetime):
                    raise TypeError(
                        f"window key must evaluate to datetime, got {type(old_time).__name__}"
                    )

            self._window.append(row)
            for ev in self._fn:
                _agg(ev).push(row)

            output = dict(row)
            for ev in self._fn:
                output[ev.out_key] = _agg(ev).value()
            return output

    def close(self) -> None:
        self._window.clear()
        self._last_time = None
        super().close()
