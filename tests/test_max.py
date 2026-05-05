from __future__ import annotations

import unittest

from walle import MaxExpr
from walle import Select


def _row(v):
    return {"v": v}


class MaxAggTests(unittest.TestCase):
    def test_returns_max(self) -> None:
        agg = MaxExpr(Select("v"))
        for v in [3, 7, 2, 7, 5]:
            agg.push(_row(v))
        self.assertEqual(agg.value(), 7)

    def test_skips_nulls(self) -> None:
        agg = MaxExpr(Select("v"))
        for v in [None, 4, None, 2]:
            agg.push(_row(v))
        self.assertEqual(agg.value(), 4)

    def test_pop_removes_oldest(self) -> None:
        agg = MaxExpr(Select("v"))
        agg.push(_row(5))
        agg.push(_row(3))
        agg.push(_row(8))
        agg.pop(_row(5))
        self.assertEqual(agg.value(), 8)

    def test_pop_drops_max_when_oldest(self) -> None:
        agg = MaxExpr(Select("v"))
        agg.push(_row(8))
        agg.push(_row(3))
        agg.pop(_row(8))
        self.assertEqual(agg.value(), 3)

    def test_empty_returns_none(self) -> None:
        self.assertIsNone(MaxExpr(Select("v")).value())

    def test_reset_clears_state(self) -> None:
        agg = MaxExpr(Select("v"))
        agg.push(_row(5))
        agg.reset()
        self.assertIsNone(agg.value())


if __name__ == "__main__":
    unittest.main()
