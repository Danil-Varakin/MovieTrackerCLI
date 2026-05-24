from __future__ import annotations

import typer

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.search import search_media
from movie_tracker.cli.errors import fail
from movie_tracker.cli.state import runtime_from_context
from movie_tracker.exceptions import MovieTrackerError
from movie_tracker.formatters.output import emit
from movie_tracker.formatters.table import media_table
from movie_tracker.utils.validators import validate_content_type, validate_limit, validate_page


def search(
    ctx: typer.Context,
    query: str = typer.Argument("", help="Строка поиска: название или ключевые слова."),
    content_type: str = typer.Option("all", "--type", help="movie | tv | all"),
    genre: str | None = typer.Option(None, "--genre", help="ID или название жанра."),
    year: int | None = typer.Option(None, "--year", help="Год выхода."),
    lang: str | None = typer.Option(None, "--lang", help="Оставлено для совместимости с ТЗ."),
    page: int = typer.Option(1, "--page", help="Номер страницы."),
    per_page: int = typer.Option(10, "--per-page", help="5 | 10 | 20 результатов."),
    sort: str = typer.Option("relevance", "--sort", help="relevance | popularity | rating | year"),
) -> None:
    """Поиск фильмов и сериалов в Kinopoisk API Unofficial."""
    runtime = runtime_from_context(ctx)
    try:
        content_type = validate_content_type(content_type)
        validate_page(page)
        validate_limit(per_page, minimum=1, maximum=20)
        if sort not in {"relevance", "popularity", "rating", "year"}:
            raise MovieTrackerError("Сортировка: relevance | popularity | rating | year")
        if not query.strip() and not genre:
            raise MovieTrackerError("Укажите строку поиска или жанр.")
        client = KinopoiskClient(runtime.config, runtime.auth_store(), runtime.cache())
        items = search_media(
            client,
            query=query,
            content_type=content_type,
            genre=genre,
            year=year,
            page=page,
            per_page=per_page,
            sort=sort,
        )
        if lang and not runtime.quiet:
            runtime.console.print(
                "Параметр --lang сохранён для совместимости; Kinopoisk API отдаёт русскоязычные поля по умолчанию.",
                style="dim",
            )
        emit(
            runtime.console,
            runtime.output_format,
            items,
            lambda console, payload: media_table(console, payload, title="Поиск"),
        )
    except MovieTrackerError as exc:
        fail(runtime, exc)
