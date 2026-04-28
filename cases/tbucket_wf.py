from pathlib import Path

from tester import (
    And,
    CsvScan,
    DateTime,
    Eq,
    Eval,
    Filter,
    Gte,
    HashAggregate,
    Int,
    LastAgg,
    Literal,
    Lte,
    Minutes,
    Select,
    Sort,
    SortKey,
    SumAgg,
    TBucket,
    TestCase,
    Timestamp,
    WindowAggregate,
)


def case(**kwargs) -> TestCase:
    return TestCase(
        Sort(
            keys=(SortKey(Select("bucket")),),
            child=HashAggregate(
                child=WindowAggregate(
                    child=Sort(
                        keys=(SortKey(Select("time")),),
                        child=Filter(
                            child=Eval(
                                "time",
                                child=DateTime(Select("@timestamp")),
                                source=CsvScan(Path(kwargs["data"])),
                            ),
                            predicate=And(
                                And(
                                    Eq(Select("dim"), Literal("a")),
                                    Gte(
                                        Select("time"),
                                        Literal(Timestamp(kwargs["start"])),
                                    ),
                                ),
                                Lte(
                                    Select("time"),
                                    Literal(Timestamp(kwargs["end"])),
                                ),
                            ),
                        ),
                    ),
                    window=Minutes(int(kwargs["window"])),
                    key=Select("time"),
                    fn=(Eval("sum", child=SumAgg(Int(Select("val")))),),
                ),
                key=(
                    Eval("dim", child=Select("dim")),
                    Eval(
                        "bucket",
                        child=TBucket(
                            Minutes(int(kwargs["step_sz"])),
                            Select("time"),
                        ),
                    ),
                ),
                fn=(Eval("sum", child=LastAgg(Select("sum"))),),
            ),
        )
    )
