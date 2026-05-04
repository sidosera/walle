from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from walle import ListScan, Operator, RateInterpolate, run


def _bucket(
    label: datetime,
    first_ts: datetime,
    first_value: float,
    last_ts: datetime,
    last_value: float,
    samples: int,
) -> dict:
    return {
        "bucket": label,
        "first_ts": first_ts,
        "first_value": first_value,
        "last_ts": last_ts,
        "last_value": last_value,
        "samples": samples,
    }


def _rates(
    child: Operator, *, label_is_right_edge: bool, step_min: int = 5
) -> list[float | None]:
    op = RateInterpolate(
        child=child,
        bucket_key="bucket",
        first_ts_key="first_ts",
        first_value_key="first_value",
        last_ts_key="last_ts",
        last_value_key="last_value",
        samples_key="samples",
        step=timedelta(minutes=step_min),
        label_is_right_edge=label_is_right_edge,
    )
    return [
        round(row["rate"], 6) if row["rate"] is not None else None for row in run(op)
    ]


def _t(*, m: int, s: int = 0) -> datetime:
    return datetime(2024, 1, 1) + timedelta(minutes=m, seconds=s)


class RateInterpolateTests(unittest.TestCase):
    def test_left_edge_two_buckets(self) -> None:
        # Bucket [0,5): samples 00:00..00:04 with counter 1..15. Bucket [5,10): 00:05..00:09, counter 21..55.
        # Bucket 0: no prev → extrapolate to lower (gap=0 → first_value); next exists →
        # interpolate to upper using next bucket's first sample. rate = (21 - 1) / 300 = 0.0667.
        # Bucket 1: prev exists → interpolate to lower (rebuilds the same 21 at boundary);
        # no next → extrapolate to upper, gap shrinks to avg/2 = 24s.
        rows = [
            _bucket(_t(m=0), _t(m=0), 1, _t(m=4), 15, 5),
            _bucket(_t(m=5), _t(m=5), 21, _t(m=9), 55, 5),
        ]
        rates = _rates(ListScan(rows), label_is_right_edge=False)
        self.assertEqual(len(rates), 2)
        self.assertIsNotNone(rates[0])
        self.assertIsNotNone(rates[1])
        assert rates[0] is not None and rates[1] is not None
        self.assertAlmostEqual(rates[0], 0.066667, places=5)
        self.assertAlmostEqual(rates[1], 0.124667, places=5)

    def test_right_edge_first_bucket_single_sample_returns_none(self) -> None:
        rows = [
            _bucket(_t(m=0), _t(m=0), 1, _t(m=0), 1, 1),
            _bucket(_t(m=5), _t(m=1), 3, _t(m=5), 21, 5),
        ]
        rates = _rates(ListScan(rows), label_is_right_edge=True)
        self.assertIsNone(rates[0])
        self.assertIsNotNone(rates[1])

    def test_zero_samples_emits_null_rate(self) -> None:
        rows = [
            _bucket(_t(m=0), _t(m=0), 0, _t(m=0), 0, 0),
        ]
        rates = _rates(ListScan(rows), label_is_right_edge=False)
        self.assertEqual(rates, [None])

    def test_streaming_does_not_buffer_all_rows(self) -> None:
        # Verify the operator pulls lazily: only after enough next() calls does it advance child.
        class CountingScan(Operator):
            def __init__(self, rows):
                super().__init__()
                self._rows = list(rows)
                self.pulled = 0

            def open(self):
                super().open()

            def next(self):
                if self.pulled >= len(self._rows):
                    return None
                row = self._rows[self.pulled]
                self.pulled += 1
                return row

            def close(self):
                super().close()

        rows = [
            _bucket(_t(m=0), _t(m=0), 1, _t(m=4), 15, 5),
            _bucket(_t(m=5), _t(m=5), 21, _t(m=9), 55, 5),
            _bucket(_t(m=10), _t(m=10), 66, _t(m=14), 120, 5),
            _bucket(_t(m=15), _t(m=15), 136, _t(m=19), 210, 5),
        ]
        scan = CountingScan(rows)
        op = RateInterpolate(
            child=scan,
            bucket_key="bucket",
            first_ts_key="first_ts",
            first_value_key="first_value",
            last_ts_key="last_ts",
            last_value_key="last_value",
            samples_key="samples",
            step=timedelta(minutes=5),
            label_is_right_edge=False,
        )
        op.open()
        # After open, RateInterpolate fills curr+next: 2 rows pulled.
        self.assertEqual(scan.pulled, 2)
        op.next()  # emit bucket 0; pull 1 more (bucket 2) for new "next"
        self.assertEqual(scan.pulled, 3)
        op.next()  # emit bucket 1; pull 1 more (bucket 3)
        self.assertEqual(scan.pulled, 4)
        op.close()


if __name__ == "__main__":
    unittest.main()
