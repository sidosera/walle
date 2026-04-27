# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

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
    TBucket,
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
                    child=TBucket(
                        Minutes(5),
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
