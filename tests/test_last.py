from __future__ import annotations

import unittest

from walle import LastAgg
from walle import Select


def _row(v):
    return {"v": v}


class LastAggTests(unittest.TestCase):
    def test_returns_last_pushed_value(self) -> None:
        agg = LastAgg(Select("v"))
        agg.push(_row(7))
        agg.push(_row(11))
        agg.push(_row(13))
        self.assertEqual(agg.value(), 13)

    def test_null_overwrites_previous(self) -> None:
        agg = LastAgg(Select("v"))
        agg.push(_row(7))
        agg.push(_row(None))
        self.assertIsNone(agg.value())

    def test_empty_returns_none(self) -> None:
        agg = LastAgg(Select("v"))
        self.assertIsNone(agg.value())

    def test_reset_clears_state(self) -> None:
        agg = LastAgg(Select("v"))
        agg.push(_row(1))
        agg.reset()
        self.assertIsNone(agg.value())


if __name__ == "__main__":
    unittest.main()
