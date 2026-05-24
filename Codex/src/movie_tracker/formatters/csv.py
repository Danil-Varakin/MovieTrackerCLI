from __future__ import annotations

import csv
import io
from collections.abc import Iterable
from typing import Any


def _flatten(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def dumps_csv(payload: Any) -> str:
    rows: list[dict[str, Any]]
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        rows = payload["items"]
    elif isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = [payload]
    elif isinstance(payload, Iterable):
        rows = list(payload)
    else:
        rows = [{"value": payload}]

    if not rows:
        return ""

    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _flatten(row.get(key)) for key in fieldnames})
    return buffer.getvalue().strip()
