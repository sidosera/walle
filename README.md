Tiny query-plan runner used as a deterministic reference engine for testing.

## Core

### Operator

Row-stream stage with `open`/`next`/`close`

### Expr

Row-local computation.


### AggregateExpr

Stateful expr with `reset`/`push`/`pop`/`value`.

### WindowedAggregate

Sliding-time driver for aggregate state.

### GroupAggregate

Hash grouping over materialized child rows.

## Plan Concepts

### Read source

```python
source = CsvScan(Path("data.csv"))
```

### Mapping input

```python
typed = Map("time", ToTimestamp(Select("@timestamp")), source=source)
```

### Filter
```python
filtered = Filter(child=typed, predicate=Eq(Select("dim"), Literal("a")))
```

### Sort
```python
ordered = Sort(child=filtered, keys=(SortKey(Select("time")),))
```

### Rolling window
```python
win = WindowedAggregate(
    child=ordered,
    window=Minutes(5),
    key=Select("time"),
    fn=(Map("sum", child=SumExpr(ToInt(Select("val")))),),
)
```

### Complex aggregations
```python
win_rate = WindowedAggregate(
    child=ordered,
    window=Minutes(5),
    key=Select("time"),
    fn=(Map("rate", child=RateExpr(ToInt(Select("counter_val")), Select("time"), Minutes(5))),),
)
bucketed = GroupAggregate(
    child=win_rate,
    key=(Map("bucket", StepCeil(Minutes(5), ToTimestamp(Literal("2024-01-01T00:00:00Z")), Select("time"))),),
    fn=(Map("rate", child=LastExpr(Select("rate"))),),
)
result = Sort(child=bucketed, keys=(SortKey(Select("bucket")),))
```

## Run

### Plan

`uv run walle-tester .cases/tbucket_wf.py data=<csv> start=<iso> end=<iso> window=<min> step_sz=<min>`


### Test

Run unit tests: `uv run test`
