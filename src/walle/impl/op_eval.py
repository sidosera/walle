from __future__ import annotations

from ..operator import Operator
from ..util import Row
from .expr import Expr


class Map(Operator[Row]):
    def __init__(
        self, out_key: str, child: Expr, *, source: Operator[Row] | None = None
    ) -> None:
        super().__init__(source)
        if out_key == "":
            raise ValueError("map out_key must be non-empty")
        self.out_key = out_key
        self.expr = child

    def next(self) -> Row | None:
        if self.child is None:
            raise RuntimeError("Map requires a child operator")
        row = self.child.next()
        if row is None:
            return None
        if not isinstance(row, dict):
            raise TypeError(f"Map expected row dict, got {type(row).__name__}")
        out = dict(row)
        out[self.out_key] = self.expr.eval(row)
        return out
