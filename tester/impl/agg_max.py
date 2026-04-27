# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

from __future__ import annotations

from collections import deque
from typing import Any

from ..agg import Agg
from ..util import Row
from .expr import Expr


class MaxAgg(Agg):
    def __init__(self, expr: Expr) -> None:
        self._expr = expr
        self._q: deque[Any] = deque()

    def reset(self) -> None:
        self._q.clear()

    def push(self, point: Row) -> None:
        v = self._expr.eval(point)
        while self._q and self._q[-1] <= v:
            self._q.pop()
        self._q.append(v)

    def pop(self, point: Row) -> None:
        v = self._expr.eval(point)
        if self._q and self._q[0] == v:
            self._q.popleft()

    def value(self) -> Any:
        return self._q[0]
