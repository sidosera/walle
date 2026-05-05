Tiny arbitrary query-plan runner for local experiments.

Model terms:
- Operators move rows (`open`/`next`/`close`).
- Expressions compute values per row.
- Aggregate functions are expression nodes (`Agg`) with windowed mutable state,
  driven by operators such as `WindowAggregate` via `push`/`pop`.
