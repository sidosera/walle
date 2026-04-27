# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

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
