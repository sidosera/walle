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
