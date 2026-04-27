# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

from __future__ import annotations

import abc
from collections.abc import Iterator
from typing import Generic, TypeVar

T = TypeVar("T")


class Operator(abc.ABC, Generic[T]):
    def __init__(self, child: Operator[object] | None = None) -> None:
        self.child = child

    def open(self) -> None:
        child = self.child
        if child is not None:
            child.open()

    @abc.abstractmethod
    def next(self) -> T | None: ...

    def close(self) -> None:
        child = self.child
        if child is not None:
            child.close()


def pull(operator: Operator[T]) -> Iterator[T]:
    while True:
        row = operator.next()
        if row is None:
            return
        yield row


def run(root: Operator[T]) -> Iterator[T]:
    try:
        root.open()
        yield from pull(root)
    finally:
        root.close()
