from __future__ import annotations

import unittest

from walle import CountExpr
from walle import Select


def _row(v):
    return {"v": v}


class CountAggTests(unittest.TestCase):
    def test_counts_non_null_values(self) -> None:
        agg = CountExpr(Select("v"))
        for v in [1, 2, None, 3, None]:
            agg.push(_row(v))
        self.assertEqual(agg.value(), 3)

    def test_counts_all_rows_without_expr(self) -> None:
        agg = CountExpr()
        for v in [1, 2, None, 3]:
            agg.push(_row(v))
        self.assertEqual(agg.value(), 4)

    def test_pop_decrements(self) -> None:
        agg = CountExpr(Select("v"))
        agg.push(_row(1))
        agg.push(_row(2))
        agg.pop(_row(1))
        self.assertEqual(agg.value(), 1)

    def test_pop_skips_null(self) -> None:
        agg = CountExpr(Select("v"))
        agg.push(_row(1))
        agg.pop(_row(None))
        self.assertEqual(agg.value(), 1)

    def test_empty_is_zero(self) -> None:
        self.assertEqual(CountExpr(Select("v")).value(), 0)

    def test_reset_clears_state(self) -> None:
        agg = CountExpr(Select("v"))
        agg.push(_row(1))
        agg.push(_row(2))
        agg.reset()
        self.assertEqual(agg.value(), 0)


if __name__ == "__main__":
    unittest.main()
