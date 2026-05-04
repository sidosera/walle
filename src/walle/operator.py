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
