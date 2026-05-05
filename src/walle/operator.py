from __future__ import annotations

import abc
from collections.abc import Iterator
from typing import Generic, TypeVar

T = TypeVar("T")


class Operator(abc.ABC, Generic[T]):
    def __init__(self, child: Operator[object] | None = None) -> None:
        self.child = child
        self._is_open = False

    def open(self) -> None:
        if self._is_open:
            raise RuntimeError(f"{type(self).__name__}.open() called twice")
        child = self.child
        if child is not None:
            child.open()
        self._is_open = True

    @abc.abstractmethod
    def next(self) -> T | None: ...

    def close(self) -> None:
        if self._is_open is False:
            return
        child = self.child
        if child is not None:
            child.close()
        self._is_open = False


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
