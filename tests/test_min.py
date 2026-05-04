from __future__ import annotations

import unittest

from walle import MinAgg
from walle import Select


def _row(v):
    return {"v": v}


class MinAggTests(unittest.TestCase):
    def test_returns_min(self) -> None:
        agg = MinAgg(Select("v"))
        for v in [3, 7, 2, 5, 2]:
            agg.push(_row(v))
        self.assertEqual(agg.value(), 2)

    def test_skips_nulls(self) -> None:
        agg = MinAgg(Select("v"))
        for v in [None, 4, None, 9]:
            agg.push(_row(v))
        self.assertEqual(agg.value(), 4)

    def test_pop_removes_oldest(self) -> None:
        agg = MinAgg(Select("v"))
        agg.push(_row(2))
        agg.push(_row(5))
        agg.push(_row(8))
        agg.pop(_row(2))
        self.assertEqual(agg.value(), 5)

    def test_empty_returns_none(self) -> None:
        self.assertIsNone(MinAgg(Select("v")).value())

    def test_reset_clears_state(self) -> None:
        agg = MinAgg(Select("v"))
        agg.push(_row(1))
        agg.reset()
        self.assertIsNone(agg.value())


if __name__ == "__main__":
    unittest.main()
