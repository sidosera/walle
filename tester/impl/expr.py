from __future__ import annotations

import abc
import operator
from datetime import datetime, timedelta
from typing import Any

from ..util import Row, mktime


class Expr(abc.ABC):
    @abc.abstractmethod
    def eval(self, row: Row) -> Any: ...


class Literal(Expr):
    def __init__(self, value: Any) -> None:
        self._value = value

    def eval(self, row: Row) -> Any:
        return self._value


class Select(Expr):
    def __init__(self, *fields: str) -> None:
        self._fields = fields

    def eval(self, row: Row) -> Any:
        if len(self._fields) == 1:
            return row[self._fields[0]]
        return tuple(row[f] for f in self._fields)


class DateTime(Expr):
    def __init__(self, child: Expr) -> None:
        self._child = child

    def eval(self, row: Row) -> Any:
        return mktime(self._child.eval(row))


class Int(Expr):
    def __init__(self, child: Expr) -> None:
        self._child = child

    def eval(self, row: Row) -> Any:
        value = self._child.eval(row)
        if value is None:
            return None
        return int(value)


class UnaryExpr(Expr):
    def __init__(self, child: Expr) -> None:
        self._child = child


class Not(UnaryExpr):
    def eval(self, row: Row) -> Any:
        value = self._child.eval(row)
        if value is None:
            return None
        return not value


class BinaryExpr(Expr):
    def __init__(self, left: Expr, right: Expr) -> None:
        self._left = left
        self._right = right

    def _values(self, row: Row) -> tuple[Any, Any]:
        return self._left.eval(row), self._right.eval(row)


class NullPropagatingBinaryExpr(BinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        raise NotImplementedError

    def eval(self, row: Row) -> Any:
        left, right = self._values(row)
        if left is None or right is None:
            return None
        return self._apply(left, right)


class Eq(NullPropagatingBinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        return left == right


class Ne(NullPropagatingBinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        return left != right


class Lt(NullPropagatingBinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        return left < right


class Lte(NullPropagatingBinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        return left <= right


class Gt(NullPropagatingBinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        return left > right


class Gte(NullPropagatingBinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        return left >= right


class Add(NullPropagatingBinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        return operator.add(left, right)


class Sub(NullPropagatingBinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        return operator.sub(left, right)


class Mul(NullPropagatingBinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        return operator.mul(left, right)


class Div(NullPropagatingBinaryExpr):
    def _apply(self, left: Any, right: Any) -> Any:
        return operator.truediv(left, right)


class And(BinaryExpr):
    def eval(self, row: Row) -> Any:
        left, right = self._values(row)
        if left is False or right is False:
            return False
        if left is None or right is None:
            return None
        return True


class Or(BinaryExpr):
    def eval(self, row: Row) -> Any:
        left, right = self._values(row)
        if left is True or right is True:
            return True
        if left is None or right is None:
            return None
        return False


class Minutes(timedelta):
    def __new__(cls, n: int) -> "Minutes":
        return super().__new__(cls, minutes=n)


def Timestamp(text: str) -> datetime:
    return mktime(text)
