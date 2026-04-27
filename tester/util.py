from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

EPOCH = datetime(1970, 1, 1)

Row = dict[str, Any]


def mktime(text: str) -> datetime:
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(
            tzinfo=None
        )
    except ValueError as exc:
        raise ValueError(f"invalid timestamp [{text}]") from exc


def format_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def duration_micros(value: timedelta) -> int:
    return (
        (value.days * 24 * 60 * 60) + value.seconds
    ) * 1_000_000 + value.microseconds


def bucket_ceil(value: datetime, step: timedelta) -> datetime:
    elapsed = duration_micros(value - EPOCH)
    step_size = duration_micros(step)

    quotient, remainder = divmod(elapsed, step_size)
    if remainder == 0:
        return value

    return EPOCH + timedelta(microseconds=(quotient + 1) * step_size)


def read_header(reader: csv.reader, path: Path) -> list[str]:
    try:
        return next(reader)
    except StopIteration as exc:
        raise ValueError(f"csv file is empty: {path}") from exc

