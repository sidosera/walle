from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import cast

from ..agg import _agg
from ..operator import Operator
from ..util import Row
from .eval import Eval
from .expr import Expr


class WindowAggregate(Operator[Row]):
    def __init__(
        self,
        child: Operator[Row],
        window: timedelta,
        key: Expr,
        fn: Sequence[Eval],
    ) -> None:
        super().__init__(child)
        self._window_size = window
        self._key = key
        self._fn: tuple[Eval, ...] = tuple(fn)
        self._window: deque[Row] = deque()

    def open(self) -> None:
        super().open()
        self._window.clear()
        for ev in self._fn:
            _agg(ev).reset()

    def next(self) -> Row | None:
        while True:
            row = self.child.next()
            if row is None:
                return None

            t = cast(datetime, self._key.eval(row))

            while (
                self._window
                and cast(datetime, self._key.eval(self._window[0]))
                <= t - self._window_size
            ):
                evicted = self._window.popleft()
                for ev in self._fn:
                    _agg(ev).pop(evicted)

            self._window.append(row)
            for ev in self._fn:
                _agg(ev).push(row)

            output = dict(row)
            for ev in self._fn:
                output[ev.out_key] = _agg(ev).value()
            return output

    def close(self) -> None:
        self._window.clear()
        super().close()
