#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import inspect
import json
import sys
from collections.abc import Iterator
from datetime import date, datetime, time
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import ParseResult, unquote, urlparse
from urllib.request import url2pathname

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from rt.impl.agg_count import CountAgg
from rt.impl.agg_last import LastAgg
from rt.impl.agg_max import MaxAgg
from rt.impl.agg_min import MinAgg
from rt.impl.agg_sum import SumAgg
from rt.impl.eval import Eval
from rt.impl.expr import (
    Add,
    And,
    DateTime,
    Eq,
    Gt,
    Gte,
    Int,
    Literal,
    Lte,
    Minutes,
    Select,
    TBucket,
    TStep,
    Timestamp,
)
from rt.impl.filter import Filter
from rt.impl.hash_aggregate import HashAggregate
from rt.impl.project import Project
from rt.impl.scan import CsvScan, ListScan
from rt.impl.sort import Sort, SortKey
from rt.impl.window_aggregate import WindowAggregate
from rt.operator import Operator, run
from rt.util import Row, format_timestamp


class TestCase:
    __slots__ = ("plan",)

    def __init__(self, plan: Operator) -> None:
        if not isinstance(plan, Operator):
            raise TypeError("TestCase plan must be an rt.operator.Operator")
        self.plan = plan


def _value_for_csv(value: Any) -> Any:
    if isinstance(value, datetime):
        return format_timestamp(value)
    return value


def run_to_stdout(plan: Operator[Row]) -> None:
    writer = csv.writer(sys.stdout, lineterminator="\n")
    iterator: Iterator[Row] = iter(run(plan))
    first = next(iterator, None)
    if first is None:
        return
    columns = tuple(first.keys())
    writer.writerow(columns)
    writer.writerow(tuple(_value_for_csv(first.get(c)) for c in columns))
    for row in iterator:
        writer.writerow(tuple(_value_for_csv(row.get(c)) for c in columns))
    sys.stdout.flush()


_SKIP_FUNCTION_NAMES = frozenset({"main"})


def _functions_defined_in_module(module: ModuleType) -> list[tuple[str, Any]]:
    """Top-level functions defined in this testcase module (sorted by name)."""
    mod_name = module.__name__
    out: list[tuple[str, Any]] = []
    for key in sorted(module.__dict__):
        if key.startswith("_") or key in _SKIP_FUNCTION_NAMES:
            continue
        obj = module.__dict__[key]
        if not inspect.isfunction(obj):
            continue
        if getattr(obj, "__module__", None) != mod_name:
            continue
        out.append((key, obj))
    return out


def _plan_from_declared(declared: Any, fn_name: str) -> Operator:
    if isinstance(declared, TestCase):
        return declared.plan
    if isinstance(declared, Operator):
        return declared
    raise SystemExit(
        f"{fn_name}() must return TestCase or Operator, got {type(declared).__name__!r}"
    )


def _parse_case_kw(tokens: list[str]) -> dict[str, str]:
    """Parse `key=value` tokens into string kwargs (values may be empty)."""
    out: dict[str, str] = {}
    for tok in tokens:
        if "=" not in tok:
            raise SystemExit(
                "each argument after the testcase path must be key=value "
                f"(kwargs), got {tok!r}"
            )
        key, sep, val = tok.partition("=")
        if not key:
            raise SystemExit(f"invalid key=value: {tok!r}")
        out[key] = val
    return out


def _invoke_testcase(fn: Any, kw: dict[str, str], name: str) -> Any:
    """Call testcase with CLI kwargs (strings); supports normal params or a single **kwargs."""
    sig = inspect.signature(fn)
    params = tuple(sig.parameters.values())
    if len(params) == 1 and params[0].kind == inspect.Parameter.VAR_KEYWORD:
        return fn(**kw)
    try:
        ba = sig.bind_partial(**kw)
    except TypeError as exc:
        raise SystemExit(
            f"{name}: CLI kwargs {kw!r} do not match signature: {exc}"
        ) from exc
    ba.apply_defaults()
    return fn(**ba.arguments)


def _row_value_for_json(value: Any) -> Any:
    if isinstance(value, datetime):
        return format_timestamp(value)
    if isinstance(value, (date, time)):
        return value.isoformat()
    return value


def _row_to_jsonable(row: Row) -> dict[str, Any]:
    return {k: _row_value_for_json(v) for k, v in row.items()}


def _resolve_local_path(ref: str) -> Path:
    p = Path(ref).expanduser()
    if not p.is_file():
        raise SystemExit(f"testcase file does not exist: {p}")
    return p.resolve()


def _path_from_file_url(parsed: ParseResult) -> Path:
    path = unquote(parsed.path)
    if (
        sys.platform == "win32"
        and path.startswith("/")
        and len(path) > 2
        and path[2] == ":"
    ):
        path = path[1:]
    return Path(url2pathname(path))


def resolve_source_path(ref: str) -> tuple[Path, str]:
    ref = ref.strip()
    if not ref:
        raise SystemExit("empty testcase reference")
    parsed = urlparse(ref)
    if parsed.scheme == "file":
        path = _path_from_file_url(parsed)
        if not path.is_file():
            raise SystemExit(f"testcase file does not exist: {path}")
        rp = path.resolve()
        return rp, str(rp)
    if parsed.scheme == "":
        path = _resolve_local_path(ref)
        return path, str(Path(ref).expanduser().resolve())
    raise SystemExit(
        f"unsupported testcase reference (use a path or file:// URL): {parsed.scheme!r}"
    )


def load_testcase_module(path: Path, key: str) -> ModuleType:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    mod_name = f"testcase_{digest}"

    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"could not create import spec for: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        sys.modules.pop(mod_name, None)
        raise SystemExit(f"module cannot be loaded: {exc}") from exc
    return module


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description="Run every top-level testcase function in a module; print one JSON object per output row."
    )
    ap.add_argument(
        "testcase", help="Path to a testcase .py file, or file:///path/to/case.py"
    )
    ap.add_argument(
        "case_kw",
        nargs="*",
        metavar="KEY=VALUE",
        default=[],
        help="Keyword arguments for each testcase function, as key=value (values are strings).",
    )
    ns = ap.parse_args(argv)

    path, key = resolve_source_path(ns.testcase)
    testcase = load_testcase_module(path, key)

    kw = _parse_case_kw(list(ns.case_kw))

    pairs = _functions_defined_in_module(testcase)
    if not pairs:
        raise SystemExit(
            "testcase module must define at least one top-level function that returns "
            "TestCase or Operator (names starting with '_' are ignored)"
        )

    for name, fn in pairs:
        try:
            declared = _invoke_testcase(fn, kw, name)
        except SystemExit:
            raise
        except Exception as exc:
            raise SystemExit(f"{name}() failed: {exc}") from exc
        root = _plan_from_declared(declared, name)
        for row in run(root):
            print(
                json.dumps(
                    {"case": name, "row": _row_to_jsonable(row)},
                    sort_keys=True,
                )
            )


if __name__ == "__main__":
    sys.modules["tester"] = sys.modules["__main__"]
    main()
