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
