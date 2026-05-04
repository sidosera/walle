"""
walle case validating ESQL's `rate(counter_val) BY TSTEP(...)` (window == bucket).

Mirrors:

    TS ts_window
    | WHERE dim == "a"
    | STATS r = rate(counter_val) BY time_bucket = TSTEP(<step>minute)

Run with:
    uv run python tester.py cases/rate_tstep_wf.py \
        data=/path/to/ts_window.csv start=2024-01-01T00:00:00Z step_sz=5
"""

from pathlib import Path

from walle import (
    CountAgg,
    CsvScan,
    DateTime,
    Eq,
    Eval,
    Filter,
    FirstAgg,
    HashAggregate,
    Int,
    LastAgg,
    Literal,
    Minutes,
    Operator,
    RateInterpolate,
    Select,
    Sort,
    SortKey,
    TStep,
    Timestamp,
)


def case(**kwargs) -> Operator:
    val = Int(Select("counter_val"))
    return RateInterpolate(
        child=Sort(
            keys=(SortKey(Select("bucket")),),
            child=HashAggregate(
                child=Eval(
                    "time",
                    child=DateTime(Select("@timestamp")),
                    source=Filter(
                        child=CsvScan(Path(kwargs["data"])),
                        predicate=Eq(Select("dim"), Literal("a")),
                    ),
                ),
                key=(
                    Eval(
                        "bucket",
                        child=TStep(
                            Minutes(int(kwargs["step_sz"])),
                            Timestamp(kwargs["start"]),
                            Select("time"),
                        ),
                    ),
                ),
                fn=(
                    Eval("first_ts", child=FirstAgg(Select("time"))),
                    Eval("first_value", child=FirstAgg(val)),
                    Eval("last_ts", child=LastAgg(Select("time"))),
                    Eval("last_value", child=LastAgg(val)),
                    Eval("samples", child=CountAgg(val)),
                ),
            ),
        ),
        bucket_key="bucket",
        first_ts_key="first_ts",
        first_value_key="first_value",
        last_ts_key="last_ts",
        last_value_key="last_value",
        samples_key="samples",
        step=Minutes(int(kwargs["step_sz"])),
        epoch=Timestamp(kwargs["start"]),
        label_is_right_edge=True,
    )
