# Copyright Elasticsearch B.V. and/or licensed to Elasticsearch B.V. under one
# or more contributor license agreements. Licensed under the "Elastic License
# 2.0", the "GNU Affero General Public License v3.0 only", and the "Server Side
# Public License v 1"; you may not use this file except in compliance with, at
# your election, the "Elastic License 2.0", the "GNU Affero General Public
# License v3.0 only", or the "Server Side Public License, v 1".

from __future__ import annotations

import csv
import sys
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from .operator import Operator, run as execute
from .util import Row, format_timestamp


def _value_for_output(value: Any) -> Any:
    if isinstance(value, datetime):
        return format_timestamp(value)
    return value


def run_to_stdout(plan: Operator[Row]) -> None:
    writer = csv.writer(sys.stdout, lineterminator="\n")
    iterator: Iterator[Row] = iter(execute(plan))
    first = next(iterator, None)
    if first is None:
        return
    columns = tuple(first.keys())
    writer.writerow(columns)
    writer.writerow(tuple(_value_for_output(first.get(c)) for c in columns))
    for row in iterator:
        writer.writerow(tuple(_value_for_output(row.get(c)) for c in columns))
    sys.stdout.flush()
