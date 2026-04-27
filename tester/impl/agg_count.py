# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

from __future__ import annotations

from ..agg import Agg
from ..util import Row


class CountAgg(Agg):
    def __init__(self) -> None:
        self._count: int = 0

    def reset(self) -> None:
        self._count = 0

    def push(self, point: Row) -> None:
        self._count += 1

    def pop(self, point: Row) -> None:
        self._count -= 1

    def value(self) -> int:
        return self._count
