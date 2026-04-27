from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from .tester import (
  And,
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
  Scan,
  Select,
  Sort,
  SortKey,
  SumAgg,
  TBucket,
  TStep,
  Timestamp,
  WindowAggregate,
)
from .tester.operator import run
from .tester.util import format_timestamp

_DATA = (
    Path(__file__).resolve().parents[2]
    / "x-pack/plugin/esql/qa/testFixtures/src/main/resources/data/ts_window_long.csv"
)

_TSTEP = "tstep"
_TBUCKET = "tbucket"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step_fn", required=True, type=int)
    parser.add_argument("--step_sz", required=True, choices=(_TBUCKET, _TSTEP))
    parser.add_argument("--window", required=True, type=int)
    parser.add_argument("--start", required=True, type=str)
    parser.add_argument("--end", required=True, type=str)
    args = parser.parse_args()

    bucket = TBucket(Minutes(args.step_sz), Select("time"))
    if args.step_fn == _TSTEP:
        bucket = TStep(Minutes(args.step_sz), Timestamp(args.start), Select("time"))

    plan = Sort(
        keys=(SortKey(Select("bucket")),),
        child=HashAggregate(
            child=WindowAggregate(
                child=Sort(
                    keys=(SortKey(Select("time")),),
                    child=Filter(
                        child=Eval(
                            "time",
                            child=DateTime(Select("@timestamp")),
                            source=Scan(_DATA),
                        ),
                        predicate=And(
                            And(
                                Eq(Select("dim"), Literal("a")),
                                Gte(Select("time"), Literal(Timestamp(args.start))),
                            ),
                            Lte(Select("time"), Literal(Timestamp(args.end))),
                        ),
                    ),
                ),
                window=Minutes(int(args.window)),
                key=Select("time"),
                fn=(Eval("sum", child=SumAgg(Int(Select("val")))),),
            ),
            key=(
                Eval("dim", child=Select("dim")),
                Eval("bucket", child=bucket),
            ),
            fn=(Eval("sum", child=LastAgg(Select("sum"))),),
        ),
    )

    out = csv.writer(sys.stdout, lineterminator="\n")
    out.writerow(("s", "dim", "bucket"))
    for row in run(plan):
        out.writerow((row["sum"], row["dim"], format_timestamp(row["bucket"])))


if __name__ == "__main__":
    main()
