# -------------------------------------------------------------
# Plan for ESQL's `sum(val) BY dim, time_bucket = TSTEP(...)`.
# -------------------------------------------------------------
from pathlib import Path

from tester import (
    And,
    CsvScan,
    ToTimestamp,
    Eq,
    Map,
    Filter,
    Gte,
    GroupAggregate,
    ToInt,
    LastExpr,
    Literal,
    Lte,
    Minutes,
    Select,
    Sort,
    SortKey,
    SumExpr,
    TestCase,
    StepCeil,
    WindowedAggregate,
)


def case(**kwargs) -> TestCase:
    return TestCase(
        Sort(
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
                            predicate=And(
                                And(
                                    Eq(Select("dim"), Literal("a")),
                                    Gte(
                                        Select("time"),
                                        ToTimestamp(Literal(kwargs["start"])),
                                    ),
                                ),
                                Lte(
                                    Select("time"),
                                    ToTimestamp(Literal(kwargs["end"])),
                                ),
                            ),
                        ),
                    ),
                    window=Minutes(int(kwargs["window"])),
                    key=Select("time"),
                    fn=(Map("sum", child=SumExpr(ToInt(Select("val")))),),
                ),
                key=(
                    Map("dim", child=Select("dim")),
                    Map(
                        "bucket",
                        child=StepCeil(
                            Minutes(int(kwargs["step_sz"])),
                            ToTimestamp(Literal(kwargs["start"])),
                            Select("time"),
                        ),
                    ),
                ),
                fn=(Map("sum", child=LastExpr(Select("sum"))),),
            ),
        )
    )
