from __future__ import annotations

import typer

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.trending import trending_media
from movie_tracker.cli.errors import fail
from movie_tracker.cli.state import runtime_from_context
from movie_tracker.exceptions import MovieTrackerError
from movie_tracker.formatters.output import emit
from movie_tracker.formatters.table import media_table
from movie_tracker.utils.validators import validate_content_type, validate_limit, validate_page


def trending(
    ctx: typer.Context,
    content_type: str = typer.Option("all", "--type", help="movie | tv | all"),
    window: str = typer.Option("day", "--window", help="day | week"),
    page: int = typer.Option(1, "--page", help="Номер страницы."),
    limit: int = typer.Option(20, "--limit", help="Количество результатов."),
) -> None:
    """Трендовый контент, адаптированный к доступным топам Kinopoisk API."""
    runtime = runtime_from_context(ctx)
    try:
        content_type = validate_content_type(content_type)
        if window not in {"day", "week"}:
            raise MovieTrackerError("Период: day | week")
        validate_page(page)
        validate_limit(limit, minimum=1, maximum=100)
        client = KinopoiskClient(runtime.config, runtime.auth_store(), runtime.cache())
        items = trending_media(
            client, content_type=content_type, window=window, page=page, limit=limit
        )
        if not runtime.quiet:
            runtime.console.print(
                "Trending адаптирован: day использует TOP_AWAIT_FILMS, week — TOP_100_POPULAR_FILMS.",
                style="dim",
            )
        emit(
            runtime.console,
            runtime.output_format,
            items,
            lambda console, payload: media_table(
                console, payload, title="Trending", show_rank=True
            ),
        )
    except MovieTrackerError as exc:
        fail(runtime, exc)
