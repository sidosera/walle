from __future__ import annotations

import abc
import operator
from datetime import datetime, timedelta
from typing import Any

from ..expr import Expr
from ..util import Row, bucket_ceil, bucket_floor, duration_micros, mktime


class Literal(Expr):
    def __init__(self, value: Any) -> None:
        self._value = value

    def eval(self, row: Row) -> Any:
        return self._value


class Select(Expr):
    def __init__(self, *fields: str) -> None:
        if not fields:
            raise ValueError("Select requires at least one field")
        if any(field == "" for field in fields):
            raise ValueError("Select field names must be non-empty")
        self._fields = fields

    def eval(self, row: Row) -> Any:
        if len(self._fields) == 1:
            field = self._fields[0]
            if field not in row:
                raise KeyError(f"missing field: {field}")
            return row[field]
        out: list[Any] = []
        for field in self._fields:
            if field not in row:
                raise KeyError(f"missing field: {field}")
            out.append(row[field])
        return tuple(out)


class ToTimestamp(Expr):
    def __init__(self, child: Expr | str) -> None:
        self._child = child

    def eval(self, row: Row) -> Any:
        value = self._child if isinstance(self._child, str) else self._child.eval(row)
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return mktime(value)
        raise TypeError(
            f"ToTimestamp expects str|datetime|None, got {type(value).__name__}"
        )


class ToInt(Expr):
    def __init__(self, child: Expr) -> None:
        self._child = child

    def eval(self, row: Row) -> Any:
        value = self._child.eval(row)
        if value is None:
            return None
        if isinstance(value, bool):
            raise TypeError("ToInt expects numeric or numeric-string input, got bool")
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


class BucketFloor(Expr):
    """Left-edge labeled bucket (matches ESQL's BUCKET / TBUCKET):
    returns the largest boundary <= value."""

    def __init__(self, size: timedelta, child: Expr) -> None:
        if size <= timedelta(0):
            raise ValueError(f"bucket size must be > 0, got {size}")
        self._size = size
        self._child = child

    def eval(self, row: Row) -> Any:
        value = self._child.eval(row)
        if value is None:
            return None
        if not isinstance(value, datetime):
            raise TypeError(
                f"BucketFloor expects datetime input, got {type(value).__name__}"
            )
        return bucket_floor(value, self._size)


class StepCeil(Expr):
    def __init__(self, size: timedelta, start: Expr | datetime, child: Expr) -> None:
        if size <= timedelta(0):
            raise ValueError(f"step size must be > 0, got {size}")
        self._size = size
        self._start = start
        self._child = child

    def eval(self, row: Row) -> Any:
        start = (
            self._start if isinstance(self._start, datetime) else self._start.eval(row)
        )
        t = self._child.eval(row)
        if start is None or t is None:
            return None
        if not isinstance(start, datetime):
            raise TypeError(
                f"StepCeil start must evaluate to datetime, got {type(start).__name__}"
            )
        if not isinstance(t, datetime):
            raise TypeError(
                f"StepCeil child must evaluate to datetime, got {type(t).__name__}"
            )
        elapsed = duration_micros(t - start)
        step_size = duration_micros(self._size)
        quotient, remainder = divmod(elapsed, step_size)
        n = quotient if remainder == 0 else quotient + 1
        return start + timedelta(microseconds=n * step_size)
