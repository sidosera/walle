from __future__ import annotations

from ..operator import Operator
from ..util import Row
from .expr import Expr


class Filter(Operator[Row]):
    def __init__(self, child: Operator[Row], predicate: Expr) -> None:
        super().__init__(child)
        self._predicate = predicate

    def next(self) -> Row | None:
        while True:
            row = self.child.next()
            if row is None:
                return None
            if self._predicate.eval(row) is True:
                return row
