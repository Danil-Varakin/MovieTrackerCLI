from __future__ import annotations

import typer

from movie_tracker.cli.state import Runtime
from movie_tracker.exceptions import MovieTrackerError


def fail(runtime: Runtime, exc: MovieTrackerError) -> None:
    runtime.console.print(str(exc), style="red")
    raise typer.Exit(exc.exit_code)
