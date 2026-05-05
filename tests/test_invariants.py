from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from walle import (
    CountExpr,
    Filter,
    Limit,
    ListScan,
    Map,
    RateExpr,
    Select,
    Sort,
    SortKey,
    SumExpr,
    ToInt,
    WindowedAggregate,
    run,
)


class InvariantTests(unittest.TestCase):
    def test_list_scan_requires_open(self) -> None:
        scan = ListScan([{"v": 1}])
        with self.assertRaises(RuntimeError):
            scan.next()

    def test_limit_requires_non_negative_params(self) -> None:
        with self.assertRaises(ValueError):
            Limit(ListScan([]), -1)
        with self.assertRaises(ValueError):
            Limit(ListScan([]), 1, offset=-1)

    def test_sort_requires_keys(self) -> None:
        with self.assertRaises(ValueError):
            Sort(ListScan([{"v": 1}]), keys=())

    def test_filter_requires_boolean_predicate_result(self) -> None:
        plan = Filter(ListScan([{"v": 1}]), Select("v"))
        with self.assertRaises(TypeError):
            list(run(plan))

    def test_select_requires_existing_field(self) -> None:
        with self.assertRaises(KeyError):
            Select("missing").eval({"v": 1})

    def test_to_int_rejects_bool(self) -> None:
        with self.assertRaises(TypeError):
            ToInt(Select("v")).eval({"v": True})

    def test_count_pop_cannot_go_negative(self) -> None:
        agg = CountExpr(Select("v"))
        with self.assertRaises(RuntimeError):
            agg.pop({"v": 1})

    def test_sum_pop_requires_matching_push(self) -> None:
        agg = SumExpr(Select("v"))
        with self.assertRaises(RuntimeError):
            agg.pop({"v": 1})

    def test_rate_requires_positive_window(self) -> None:
        with self.assertRaises(ValueError):
            RateExpr(Select("v"), Select("t"), timedelta(0))

    def test_rate_rejects_non_numeric_value(self) -> None:
        agg = RateExpr(Select("v"), Select("t"), timedelta(seconds=10))
        with self.assertRaises(TypeError):
            agg.push({"t": datetime(2024, 1, 1), "v": "bad"})

    def test_window_requires_sorted_time(self) -> None:
        window = timedelta(seconds=60)
        plan = WindowedAggregate(
            child=ListScan(
                [
                    {"t": datetime(2024, 1, 1, 0, 1), "v": 1},
                    {"t": datetime(2024, 1, 1, 0, 0), "v": 2},
                ]
            ),
            window=window,
            key=Select("t"),
            fn=(Map("sum", child=SumExpr(Select("v"))),),
        )
        with self.assertRaises(ValueError):
            list(run(plan))


if __name__ == "__main__":
    unittest.main()
