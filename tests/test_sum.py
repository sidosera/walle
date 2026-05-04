from __future__ import annotations

import unittest

from walle import SumAgg
from walle import Select


def _row(v):
    return {"v": v}


class SumAggTests(unittest.TestCase):
    def test_sums_non_null(self) -> None:
        agg = SumAgg(Select("v"))
        for v in [1, 2, None, 3]:
            agg.push(_row(v))
        self.assertEqual(agg.value(), 6)

    def test_pop_subtracts(self) -> None:
        agg = SumAgg(Select("v"))
        agg.push(_row(5))
        agg.push(_row(7))
        agg.pop(_row(5))
        self.assertEqual(agg.value(), 7)

    def test_empty_returns_none(self) -> None:
        self.assertIsNone(SumAgg(Select("v")).value())

    def test_only_nulls_returns_none(self) -> None:
        agg = SumAgg(Select("v"))
        agg.push(_row(None))
        agg.push(_row(None))
        self.assertIsNone(agg.value())

    def test_reset_clears_state(self) -> None:
        agg = SumAgg(Select("v"))
        agg.push(_row(10))
        agg.reset()
        self.assertIsNone(agg.value())


if __name__ == "__main__":
    unittest.main()
