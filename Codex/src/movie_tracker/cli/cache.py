from __future__ import annotations

import typer

from movie_tracker.cli.state import runtime_from_context

app = typer.Typer(help="Управление локальным кэшем.")


@app.command("clear")
def clear(
    ctx: typer.Context,
    older_than: int | None = typer.Option(
        None, "--older-than", help="Удалить записи старше N часов."
    ),
) -> None:
    """Очистить кэш API-запросов."""
    runtime = runtime_from_context(ctx)
    removed = runtime.cache().clear(older_than_hours=older_than)
    runtime.console.print(f"Удалено записей кэша: {removed}", style="green")
