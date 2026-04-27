# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

from __future__ import annotations

from datetime import timedelta
from typing import Any

from ..util import Row, bucket_ceil
from .expr import Expr


class TBucket(Expr):
    def __init__(self, size: timedelta, child: Expr) -> None:
        self._size = size
        self._child = child

    def eval(self, row: Row) -> Any:
        return bucket_ceil(self._child.eval(row), self._size)
