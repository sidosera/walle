# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any

from .impl.expr import Expr
from .util import Row

if TYPE_CHECKING:
    from .impl.eval import Eval


class Agg(Expr, abc.ABC):
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


def _agg(ev: Eval) -> Agg:
    assert isinstance(ev.expr, Agg)
    return ev.expr
