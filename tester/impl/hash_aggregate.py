# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

from __future__ import annotations

from collections.abc import Sequence

from ..agg import _agg
from ..operator import Operator
from ..util import Row
from .eval import Eval


class HashAggregate(Operator[Row]):
    def __init__(
        self, child: Operator[Row], key: Sequence[Eval], fn: Sequence[Eval]
    ) -> None:
        super().__init__(child)
        self._key: tuple[Eval, ...] = tuple(key)
        self._fn: tuple[Eval, ...] = tuple(fn)
        self._last_row: Row | None = None
        self._done: bool = False

    def _group_key(self, row: Row) -> tuple:
        return tuple(ev.expr.eval(row) for ev in self._key)

    def _emit_row(self) -> Row:
        assert self._last_row is not None
        out: Row = {}
        for ev in self._key:
            out[ev.out_key] = ev.expr.eval(self._last_row)
        for ev in self._fn:
            out[ev.out_key] = _agg(ev).value()
        return out

    def open(self) -> None:
        super().open()
        self._last_row = None
        for ev in self._fn:
            _agg(ev).reset()
        self._done = False

    def next(self) -> Row | None:
        if self._done:
            return None
        while True:
            row = self.child.next()
            if row is None:
                self._done = True
                if self._last_row is None:
                    return None
                return self._emit_row()
            if self._last_row is None or self._group_key(row) != self._group_key(
                self._last_row
            ):
                result = (
                    self._emit_row() if self._last_row is not None else None
                )
                for ev in self._fn:
                    _agg(ev).reset()
                self._last_row = row
                for ev in self._fn:
                    _agg(ev).push(row)
                if result is not None:
                    return result
            else:
                self._last_row = row
                for ev in self._fn:
                    _agg(ev).push(row)

    def close(self) -> None:
        self._last_row = None
        for ev in self._fn:
            _agg(ev).reset()
        self._done = False
        super().close()
