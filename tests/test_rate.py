from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from walle import Map, ListScan, RateExpr, Select, WindowedAggregate, run


class RateAggTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = datetime(2024, 1, 1)

    def _row(self, seconds: int, value: int | float | None) -> dict[str, object]:
        return {
            "time": self.base + timedelta(seconds=seconds),
            "v": value,
        }

    def _last_rate(
        self, points: list[tuple[int, int | float | None]], window_seconds: int
    ) -> float | None:
        window = timedelta(seconds=window_seconds)
        plan = WindowedAggregate(
            child=ListScan([self._row(s, v) for s, v in points]),
            window=window,
            key=Select("time"),
            fn=(Map("rate", child=RateExpr(Select("v"), Select("time"), window)),),
        )
        rows = list(run(plan))
        return rows[-1]["rate"] if rows else None

    def test_aligned_samples(self) -> None:
        self.assertEqual(self._last_rate([(0, 0), (30, 30), (60, 60)], 60), 1.0)

    def test_counter_reset(self) -> None:
        self.assertEqual(
            self._last_rate([(0, 0), (30, 50), (60, 10), (90, 40)], 90), 2 / 3
        )

    def test_start_gap_extrapolation(self) -> None:
        self.assertEqual(self._last_rate([(80, 80), (100, 100)], 100), 0.3)

    def test_end_gap_with_null_current_sample(self) -> None:
        self.assertEqual(self._last_rate([(10, 10), (30, 30), (60, None)], 60), 2 / 3)

    def test_single_sample_returns_none(self) -> None:
        self.assertIsNone(self._last_rate([(0, 1)], 60))

    def test_unsorted_input_raises(self) -> None:
        window = timedelta(seconds=60)
        plan = WindowedAggregate(
            child=ListScan([self._row(60, 60), self._row(30, 30)]),
            window=window,
            key=Select("time"),
            fn=(Map("rate", child=RateExpr(Select("v"), Select("time"), window)),),
        )
        with self.assertRaises(ValueError):
            list(run(plan))


if __name__ == "__main__":
    unittest.main()
