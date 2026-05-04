from __future__ import annotations

from datetime import datetime, timedelta

from ..operator import Operator
from ..util import Row, duration_micros


_MICROS_PER_SECOND = 1_000_000


def _to_seconds(t: datetime, epoch: datetime) -> float:
    return duration_micros(t - epoch) / _MICROS_PER_SECOND


def _extrapolate(
    first_ts_s: float,
    first_v: float,
    last_ts_s: float,
    last_v: float,
    samples: int,
    boundary_s: float,
    is_lower: bool,
) -> float:
    span = last_ts_s - first_ts_s
    avg = span / samples
    slope = (last_v - first_v) / span if span > 0 else 0.0
    if is_lower:
        gap = first_ts_s - boundary_s
        if gap <= 0:
            return first_v
        if gap > avg * 1.1:
            gap = avg / 2.0
        return max(0.0, first_v - gap * slope)
    gap = boundary_s - last_ts_s
    if gap <= 0:
        return last_v
    if gap > avg * 1.1:
        gap = avg / 2.0
    return last_v + gap * slope


def _interpolate(
    lower_last_ts_s: float,
    lower_last_v: float,
    upper_first_ts_s: float,
    upper_first_v: float,
    boundary_s: float,
    is_lower: bool,
) -> float:
    span = upper_first_ts_s - lower_last_ts_s
    delta = (
        upper_first_v - lower_last_v if upper_first_v >= lower_last_v else upper_first_v
    )
    slope = delta / span if span > 0 else 0.0
    if is_lower:
        base = lower_last_v if upper_first_v >= lower_last_v else 0.0
        return base + slope * (boundary_s - lower_last_ts_s)
    return lower_last_v + slope * (boundary_s - lower_last_ts_s)


class RateInterpolate(Operator[Row]):
    def __init__(
        self,
        child: Operator[Row],
        bucket_key: str,
        first_ts_key: str,
        first_value_key: str,
        last_ts_key: str,
        last_value_key: str,
        samples_key: str,
        step: timedelta,
        rate_out_key: str = "rate",
        epoch: datetime | None = None,
        label_is_right_edge: bool = True,
    ) -> None:
        super().__init__(child)
        self._bucket_key = bucket_key
        self._first_ts_key = first_ts_key
        self._first_value_key = first_value_key
        self._last_ts_key = last_ts_key
        self._last_value_key = last_value_key
        self._samples_key = samples_key
        self._step = step
        self._rate_out_key = rate_out_key
        self._epoch = epoch
        self._label_is_right_edge = label_is_right_edge
        self._prev: Row | None = None
        self._curr: Row | None = None
        self._next: Row | None = None
        self._epoch_resolved: datetime | None = None

    def open(self) -> None:
        super().open()
        self._curr = self.child.next() if self.child else None
        self._next = self.child.next() if self.child and self._curr else None
        self._epoch_resolved = self._epoch or (
            self._curr[self._bucket_key] if self._curr else datetime.fromtimestamp(0)
        )

    def next(self) -> Row | None:
        if self._curr is None:
            return None
        out = self._emit(self._prev, self._curr, self._next)
        self._prev = self._curr
        self._curr = self._next
        self._next = self.child.next() if self.child and self._curr else None
        return out

    def close(self) -> None:
        self._prev = None
        self._curr = None
        self._next = None
        super().close()

    def _emit(self, prev: Row | None, curr: Row, nxt: Row | None) -> Row:
        new_row = dict(curr)
        samples = curr.get(self._samples_key) or 0
        if samples < 1:
            new_row[self._rate_out_key] = None
            return new_row

        epoch = self._epoch_resolved
        label = curr[self._bucket_key]
        if self._label_is_right_edge:
            tbucket_start = _to_seconds(label - self._step, epoch)
            tbucket_end = _to_seconds(label, epoch)
        else:
            tbucket_start = _to_seconds(label, epoch)
            tbucket_end = _to_seconds(label + self._step, epoch)

        first_ts = _to_seconds(curr[self._first_ts_key], epoch)
        first_v = float(curr[self._first_value_key])
        last_ts = _to_seconds(curr[self._last_ts_key], epoch)
        last_v = float(curr[self._last_value_key])

        prev_samples = (prev.get(self._samples_key) or 0) if prev else 0
        next_samples = (nxt.get(self._samples_key) or 0) if nxt else 0

        if prev_samples == 0:
            if samples == 1:
                first_value = first_v
                first_ts_s = first_ts
            else:
                first_value = _extrapolate(
                    first_ts,
                    first_v,
                    last_ts,
                    last_v,
                    samples,
                    tbucket_start,
                    True,
                )
                first_ts_s = tbucket_start
        else:
            first_value = _interpolate(
                _to_seconds(prev[self._last_ts_key], epoch),
                float(prev[self._last_value_key]),
                first_ts,
                first_v,
                tbucket_start,
                True,
            )
            first_ts_s = tbucket_start

        if next_samples == 0:
            if samples == 1:
                last_value = last_v
                last_ts_s = last_ts
            else:
                last_value = _extrapolate(
                    first_ts,
                    first_v,
                    last_ts,
                    last_v,
                    samples,
                    tbucket_end,
                    False,
                )
                last_ts_s = tbucket_end
        else:
            last_value = _interpolate(
                last_ts,
                last_v,
                _to_seconds(nxt[self._first_ts_key], epoch),
                float(nxt[self._first_value_key]),
                tbucket_end,
                False,
            )
            last_ts_s = tbucket_end

        if last_ts_s == first_ts_s:
            new_row[self._rate_out_key] = None
        else:
            new_row[self._rate_out_key] = (last_value - first_value) / (
                last_ts_s - first_ts_s
            )
        return new_row
