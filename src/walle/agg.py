from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

from .impl.expr import Expr
from .util import Row

if TYPE_CHECKING:
    from .impl.op_eval import Map


class AggregateExpr(Expr, abc.ABC):
    def eval(self, row: Row) -> Any:
        return self.value()

    @abc.abstractmethod
    def reset(self) -> None: ...

    @abc.abstractmethod
    def push(self, point: Row) -> None: ...

    @abc.abstractmethod
    def pop(self, point: Row) -> None: ...

    @abc.abstractmethod
    def value(self) -> Any: ...


def _agg(ev: Map) -> AggregateExpr:
    if not isinstance(ev.expr, AggregateExpr):
        raise TypeError(
            f"expected AggregateExpr in aggregate map, got {type(ev.expr).__name__}"
        )
    return ev.expr
