from __future__ import annotations

from collections.abc import Sequence

from ..operator import Operator
from ..util import Row
from .op_eval import Eval


class Project(Operator[Row]):
    def __init__(self, child: Operator[Row], expressions: Sequence[Eval]) -> None:
        super().__init__(child)
        self._expressions: tuple[Eval, ...] = tuple(expressions)

    def next(self) -> Row | None:
        row = self.child.next()
        if row is None:
            return None
        return {expr.out_key: expr.expr.eval(row) for expr in self._expressions}
