from __future__ import annotations

from collections.abc import Callable
from typing import Any

from rich.console import Console

from movie_tracker.formatters.csv import dumps_csv
from movie_tracker.formatters.json import dumps_json


def emit(
    console: Console,
    output_format: str,
    payload: Any,
    table_renderer: Callable[[Console, Any], None],
) -> None:
    if output_format == "json":
        console.print(dumps_json(payload))
        return
    if output_format == "csv":
        console.print(dumps_csv(payload))
        return
    table_renderer(console, payload)
