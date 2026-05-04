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

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_PARENT = _ROOT.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))


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


_IGNORED_FIXTURE = frozenset({"main"})


def _fixtures(module: ModuleType) -> list[tuple[str, Any]]:
    mod_name = module.__name__
    out: list[tuple[str, Any]] = []
    for key in sorted(module.__dict__):
        if key.startswith("_") or key in _IGNORED_FIXTURE:
            continue
        obj = module.__dict__[key]
        if not inspect.isfunction(obj):
            continue
        if getattr(obj, "__module__", None) != mod_name:
            continue
        out.append((key, obj))
    return out


def _plan_from_declared(declared: Any, fn_name: str) -> Operator:
    if isinstance(declared, Operator):
        return declared

    raise SystemExit(
        f"{fn_name}() must return Operator, got {type(declared).__name__!r}"
    )


def _parse_case_kw(tokens: list[str]) -> dict[str, str]:
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


def _invoke_operator(fn: Any, kw: dict[str, str], name: str) -> Any:
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


def resolve_source_path(ref: str) -> tuple[Path, str]:
    ref = ref.strip()
    if not ref:
        raise SystemExit("empty testcase reference")

    path = _resolve_local_path(ref)
    return path, str(Path(ref).expanduser().resolve())


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
    ap = argparse.ArgumentParser(description="walle")
    ap.add_argument("testcase", help="Path to a testcase file")
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

    pairs = _fixtures(testcase)
    if not pairs:
        raise SystemExit(
            "testcase module must define at least one top-level function that returns Operator"
        )

    for name, fn in pairs:
        try:
            declared = _invoke_operator(fn, kw, name)
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
