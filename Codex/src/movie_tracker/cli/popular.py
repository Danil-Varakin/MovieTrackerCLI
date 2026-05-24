from __future__ import annotations

import typer

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.popular import popular_media
from movie_tracker.cli.errors import fail
from movie_tracker.cli.state import runtime_from_context
from movie_tracker.exceptions import MovieTrackerError
from movie_tracker.formatters.output import emit
from movie_tracker.formatters.table import media_table
from movie_tracker.utils.validators import validate_content_type, validate_limit, validate_page


def popular(
    ctx: typer.Context,
    content_type: str = typer.Option("movie", "--type", help="movie | tv"),
    region: str | None = typer.Option(None, "--region", help="Оставлено для совместимости с ТЗ."),
    page: int = typer.Option(1, "--page", help="Номер страницы."),
    limit: int = typer.Option(20, "--limit", help="Количество результатов."),
) -> None:
    """Популярный контент из доступных топов Kinopoisk API."""
    runtime = runtime_from_context(ctx)
    try:
        content_type = validate_content_type(content_type, allow_all=False)
        validate_page(page)
        validate_limit(limit, minimum=1, maximum=100)
        client = KinopoiskClient(runtime.config, runtime.auth_store(), runtime.cache())
        items = popular_media(client, content_type=content_type, page=page, limit=limit)
        if region and not runtime.quiet:
            runtime.console.print(
                "Kinopoisk API Unofficial не поддерживает региональный popular как TMDB; регион проигнорирован.",
                style="dim",
            )
        emit(
            runtime.console,
            runtime.output_format,
            items,
            lambda console, payload: media_table(
                console, payload, title="Популярное", show_rank=True
            ),
        )
    except MovieTrackerError as exc:
        fail(runtime, exc)
