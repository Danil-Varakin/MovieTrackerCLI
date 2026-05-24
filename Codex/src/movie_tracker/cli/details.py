from __future__ import annotations

import typer

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.details import fetch_details
from movie_tracker.cli.errors import fail
from movie_tracker.cli.state import runtime_from_context
from movie_tracker.exceptions import MovieTrackerError
from movie_tracker.formatters.output import emit
from movie_tracker.formatters.table import details_view
from movie_tracker.utils.validators import validate_content_type, validate_page


def details(
    ctx: typer.Context,
    item_id: int = typer.Argument(..., help="Kinopoisk ID фильма или сериала."),
    content_type: str | None = typer.Option(
        None, "--type", help="movie | tv; оставлено для совместимости."
    ),
    section: str = typer.Option("all", "--section", help="info | cast | reviews | similar | all"),
    lang: str | None = typer.Option(None, "--lang", help="Оставлено для совместимости с ТЗ."),
    reviews_page: int = typer.Option(1, "--reviews-page", help="Страница рецензий."),
) -> None:
    """Детальная информация по Kinopoisk ID."""
    runtime = runtime_from_context(ctx)
    try:
        if content_type:
            validate_content_type(content_type, allow_all=False)
        if section not in {"info", "cast", "reviews", "similar", "all"}:
            raise MovieTrackerError("Секция: info | cast | reviews | similar | all")
        validate_page(reviews_page)
        client = KinopoiskClient(runtime.config, runtime.auth_store(), runtime.cache())
        payload = fetch_details(client, item_id, section=section, reviews_page=reviews_page)
        if lang and not runtime.quiet:
            runtime.console.print(
                "Параметр --lang сохранён для совместимости; Kinopoisk API не принимает язык как TMDB.",
                style="dim",
            )
        emit(runtime.console, runtime.output_format, payload, details_view)
    except MovieTrackerError as exc:
        fail(runtime, exc)
