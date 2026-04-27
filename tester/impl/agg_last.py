# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

from __future__ import annotations

from typing import Any

from ..agg import Agg
from ..util import Row
from .expr import Expr


class LastAgg(Agg):
    def __init__(self, child: Expr) -> None:
        self._expr = child
        self._val: Any = None

    def reset(self) -> None:
        self._val = None

    def push(self, point: Row) -> None:
        self._val = self._expr.eval(point)

    def pop(self, point: Row) -> None:
        pass

    def value(self) -> Any:
        return self._val
