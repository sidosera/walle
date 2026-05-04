from __future__ import annotations

import copy
from collections.abc import Sequence

from ..agg import _agg
from ..operator import Operator, pull
from ..util import Row
from .op_eval import Eval


class HashAggregate(Operator[Row]):
    def __init__(
        self, child: Operator[Row], key: Sequence[Eval], fn: Sequence[Eval]
    ) -> None:
        super().__init__(child)
        self._key: tuple[Eval, ...] = tuple(key)
        self._fn: tuple[Eval, ...] = tuple(fn)
        self._rows: list[Row] = []
        self._index: int = 0

    def _group_key(self, row: Row) -> tuple:
        return tuple(ev.expr.eval(row) for ev in self._key)

    def open(self) -> None:
        super().open()
        groups: dict[tuple, tuple[Row, tuple[Eval, ...]]] = {}
        for row in pull(self.child):
            key = self._group_key(row)
            if key not in groups:
                group_row = {ev.out_key: ev.expr.eval(row) for ev in self._key}
                group_aggs = tuple(copy.deepcopy(ev) for ev in self._fn)
                for group_agg in group_aggs:
                    _agg(group_agg).reset()
                groups[key] = (group_row, group_aggs)
            _, group_aggs = groups[key]
            for group_agg in group_aggs:
                _agg(group_agg).push(row)

        self._rows = []
        for group_row, group_aggs in groups.values():
            out = dict(group_row)
            for group_agg in group_aggs:
                out[group_agg.out_key] = _agg(group_agg).value()
            self._rows.append(out)
        self._index = 0

    def next(self) -> Row | None:
        if self._index >= len(self._rows):
            return None
        row = self._rows[self._index]
        self._index += 1
        return row

    def close(self) -> None:
        self._rows.clear()
        self._index = 0
        super().close()
