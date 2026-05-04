from __future__ import annotations

import unittest

from walle import FirstAgg
from walle import Select


def _row(v):
    return {"v": v}


class FirstAggTests(unittest.TestCase):
    def test_returns_first_pushed_value(self) -> None:
        agg = FirstAgg(Select("v"))
        agg.push(_row(7))
        agg.push(_row(11))
        agg.push(_row(13))
        self.assertEqual(agg.value(), 7)

    def test_skips_leading_nulls(self) -> None:
        agg = FirstAgg(Select("v"))
        agg.push(_row(None))
        agg.push(_row(None))
        agg.push(_row(42))
        agg.push(_row(99))
        self.assertEqual(agg.value(), 42)

    def test_empty_returns_none(self) -> None:
        agg = FirstAgg(Select("v"))
        self.assertIsNone(agg.value())

    def test_all_null_returns_none(self) -> None:
        agg = FirstAgg(Select("v"))
        agg.push(_row(None))
        agg.push(_row(None))
        self.assertIsNone(agg.value())

    def test_reset_clears_state(self) -> None:
        agg = FirstAgg(Select("v"))
        agg.push(_row(1))
        agg.reset()
        agg.push(_row(2))
        self.assertEqual(agg.value(), 2)


if __name__ == "__main__":
    unittest.main()
