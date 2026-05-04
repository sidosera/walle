from __future__ import annotations

import abc
from typing import Any
from .util import Row


class Expr(abc.ABC):
    @abc.abstractmethod
    def eval(self, row: Row) -> Any: ...
