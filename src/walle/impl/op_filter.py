from __future__ import annotations

from ..operator import Operator
from ..util import Row
from .expr import Expr


class Filter(Operator[Row]):
    def __init__(self, child: Operator[Row], predicate: Expr) -> None:
        super().__init__(child)
        self._predicate = predicate

    def next(self) -> Row | None:
        if self.child is None:
            raise RuntimeError("Filter requires a child operator")
        while True:
            row = self.child.next()
            if row is None:
                return None
            if not isinstance(row, dict):
                raise TypeError(f"Filter expected row dict, got {type(row).__name__}")
            value = self._predicate.eval(row)
            if value is True:
                return row
            if value is not False and value is not None:
                raise TypeError(
                    f"Filter predicate must evaluate to bool|None, got {type(value).__name__}"
                )
