from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from rt.impl.agg_increase import IncreaseAgg
from rt.impl.expr import Select


class IncreaseAggTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = datetime(2020, 1, 1)

    def _row(self, seconds: int, value: int | float | None) -> dict[str, object]:
        return {
            "time": self.base + timedelta(seconds=seconds),
            "v": value,
        }

    def _value(self, points: list[tuple[int, int | float | None]], window_seconds: int) -> float | None:
        window = timedelta(seconds=window_seconds)
        agg = IncreaseAgg(Select("v"), Select("time"), window)
        for seconds, value in points:
            agg.push(self._row(seconds, value))
        return agg.value()

    def test_aligned_samples(self) -> None:
        self.assertEqual(self._value([(0, 0), (30, 30), (60, 60)], 60), 60.0)

    def test_counter_reset(self) -> None:
        self.assertEqual(self._value([(0, 0), (30, 50), (60, 10), (90, 40)], 90), 90.0)

    def test_multiple_counter_resets(self) -> None:
        self.assertEqual(
            self._value([(0, 0), (30, 100), (60, 20), (90, 70), (120, 10)], 120),
            180.0,
        )

    def test_start_gap_extrapolation(self) -> None:
        self.assertEqual(self._value([(80, 80), (100, 100)], 100), 30.0)

    def test_end_gap_extrapolation(self) -> None:
        self.assertEqual(self._value([(0, 0), (20, 20), (100, None)], 100), 30.0)

    def test_both_edge_gaps_extrapolation(self) -> None:
        self.assertEqual(self._value([(40, 40), (60, 60), (100, None)], 100), 40.0)

    def test_zero_crossing_clamps_left_extrapolation(self) -> None:
        self.assertEqual(self._value([(80, 5), (100, 25)], 100), 25.0)

    def test_null_mid_window_sample_is_ignored(self) -> None:
        self.assertEqual(self._value([(0, 0), (30, None), (60, 60)], 60), 60.0)

    def test_end_gap_with_null_current_sample(self) -> None:
        self.assertEqual(self._value([(10, 10), (30, 30), (60, None)], 60), 40.0)

    def test_single_sample_returns_none(self) -> None:
        self.assertIsNone(self._value([(0, 1)], 60))

    def test_unsorted_input_raises(self) -> None:
        window = timedelta(seconds=60)
        agg = IncreaseAgg(Select("v"), Select("time"), window)
        agg.push(self._row(60, 60))
        with self.assertRaises(ValueError):
            agg.push(self._row(30, 30))


if __name__ == "__main__":
    unittest.main()
