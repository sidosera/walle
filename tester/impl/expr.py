# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

from __future__ import annotations

import abc
from datetime import datetime, timedelta
from typing import Any

from ..util import Row, mktime


class Expr(abc.ABC):
    @abc.abstractmethod
    def eval(self, row: Row) -> Any: ...


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
        return int(self._child.eval(row))


class Minutes(timedelta):
    def __new__(cls, n: int) -> "Minutes":
        return super().__new__(cls, minutes=n)


def Timestamp(text: str) -> datetime:
    return mktime(text)
