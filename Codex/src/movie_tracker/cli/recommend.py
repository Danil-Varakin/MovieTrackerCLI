from __future__ import annotations

import typer

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.recommendations import recommend_by_id, recommend_by_profile
from movie_tracker.cli.errors import fail
from movie_tracker.cli.state import runtime_from_context
from movie_tracker.exceptions import MovieTrackerError
from movie_tracker.formatters.output import emit
from movie_tracker.formatters.table import media_table
from movie_tracker.utils.helpers import parse_tags
from movie_tracker.utils.validators import validate_content_type, validate_limit, validate_page


def recommend(
    ctx: typer.Context,
    based_on: int | None = typer.Option(None, "--based-on", help="Рекомендации по Kinopoisk ID."),
    content_type: str = typer.Option("all", "--type", help="movie | tv | all"),
    genres: str | None = typer.Option(None, "--genres", help="Жанры через запятую."),
    exclude_watched: bool = typer.Option(False, "--exclude-watched", help="Исключить watched."),
    limit: int = typer.Option(10, "--limit", help="Количество рекомендаций."),
    page: int = typer.Option(1, "--page", help="Номер страницы."),
) -> None:
    """Получить рекомендации по ID, жанрам или локальному watchlist."""
    runtime = runtime_from_context(ctx)
    try:
        content_type = validate_content_type(content_type)
        validate_limit(limit, minimum=1, maximum=40)
        validate_page(page)
        client = KinopoiskClient(runtime.config, runtime.auth_store(), runtime.cache())
        if based_on:
            items = recommend_by_id(client, based_on, limit=limit)
        else:
            items = recommend_by_profile(
                client,
                runtime.watchlist(),
                content_type=content_type,
                genres=parse_tags(genres),
                exclude_watched=exclude_watched,
                limit=limit,
                page=page,
            )
        emit(
            runtime.console,
            runtime.output_format,
            items,
            lambda console, payload: media_table(
                console, payload, title="Рекомендации", show_description=True
            ),
        )
    except MovieTrackerError as exc:
        fail(runtime, exc)
