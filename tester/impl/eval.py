from __future__ import annotations

from ..operator import Operator
from ..util import Row
from .expr import Expr


class Eval(Operator[Row]):
    def __init__(
        self, out_key: str, child: Expr, *, source: Operator[Row] | None = None
    ) -> None:
        super().__init__(source)
        self.out_key = out_key
        self.expr = child

    def next(self) -> Row | None:
        row = self.child.next()
        if row is None:
            return None
        out = dict(row)
        out[self.out_key] = self.expr.eval(row)
        return out
