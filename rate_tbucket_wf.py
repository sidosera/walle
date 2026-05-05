# -------------------------------------------------------------
# Plan for ESQL's `rate(counter_val) BY dim, time_bucket = BucketFloor(...)`.
# -------------------------------------------------------------

from pathlib import Path

from walle import (
    CsvScan,
    ToTimestamp,
    Eq,
    Map,
    Filter,
    GroupAggregate,
    ToInt,
    LastExpr,
    Literal,
    Minutes,
    Operator,
    RateExpr,
    Select,
    Sort,
    SortKey,
    BucketFloor,
    WindowedAggregate,
)


def case(**kwargs) -> Operator:
    val = ToInt(Select("counter_val"))
    window = Minutes(int(kwargs.get("window", kwargs["step_sz"])))
    return Sort(
        keys=(SortKey(Select("bucket")),),
        child=GroupAggregate(
            child=WindowedAggregate(
                child=Sort(
                    keys=(SortKey(Select("time")),),
                    child=Filter(
                        child=Map(
                            "time",
                            child=ToTimestamp(Select("@timestamp")),
                            source=CsvScan(Path(kwargs["data"])),
                        ),
                        predicate=Eq(Select("dim"), Literal(kwargs.get("dim", "a"))),
                    ),
                ),
                window=window,
                key=Select("time"),
                fn=(Map("rate", child=RateExpr(val, Select("time"), window)),),
            ),
            key=(
                Map(
                    "bucket",
                    child=BucketFloor(
                        Minutes(int(kwargs["step_sz"])),
                        Select("time"),
                    ),
                ),
            ),
            fn=(Map("rate", child=LastExpr(Select("rate"))),),
        ),
    )
