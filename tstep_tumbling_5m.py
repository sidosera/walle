from __future__ import annotations

from pathlib import Path

from .tester import (
    CountAgg,
    DateTime,
    Eval,
    HashAggregate,
    Int,
    LastAgg,
    MaxAgg,
    MinAgg,
    Minutes,
    Scan,
    Select,
    Sort,
    SumAgg,
    Timestamp,
    TStep,
    WindowAggregate,
    run_to_stdout,
)

_DATA = (
    Path(__file__).resolve().parents[2]
    / "x-pack/plugin/esql/qa/testFixtures/src/main/resources/data/ts_window.csv"
)

if __name__ == "__main__":
    plan = Sort(
        child=HashAggregate(
            child=WindowAggregate(
                child=Sort(
                    child=Eval(
                        "time",
                        child=DateTime(Select("@timestamp")),
                        source=Scan(_DATA),
                    ),
                    key=Select("dim", "time"),
                ),
                window=Minutes(5),
                key=Select("time"),
                fn=(
                    Eval("sum", child=SumAgg(Int(Select("val")))),
                    Eval("count", child=CountAgg()),
                    Eval("max", child=MaxAgg(Int(Select("val")))),
                    Eval("min", child=MinAgg(Int(Select("val")))),
                ),
            ),
            key=(
                Eval("dim", child=Select("dim")),
                Eval(
                    "time_bucket",
                    child=TStep(
                        Minutes(5),
                        Timestamp("2024-01-01T00:00:00.000Z"),
                        Select("time"),
                    ),
                ),
            ),
            fn=(
                Eval("sum", child=LastAgg(Select("sum"))),
                Eval("count", child=LastAgg(Select("count"))),
                Eval("max", child=LastAgg(Select("max"))),
                Eval("min", child=LastAgg(Select("min"))),
            ),
        ),
        key=Select("time_bucket", "dim"),
    )
    run_to_stdout(plan)
