"""CLI команда: search — поиск фильмов и сериалов через Кинопоиск API."""

from __future__ import annotations

import asyncio
from typing import Optional

import typer

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.search import (
    discover_movies,
    discover_tv,
    get_genres,
    search_movies,
    search_multi,
    search_tv,
)
from movie_tracker.cache.manager import (
    TTL_SEARCH,
    cache_get,
    cache_set,
    make_search_key,
)
from movie_tracker.config import get_api_key, get_language
from movie_tracker.exceptions import MovieTrackerError
from movie_tracker.formatters.table import error, info, print_search_results
from movie_tracker.utils.validators import validate_page, validate_year

app = typer.Typer()


async def _fetch_genres(client: KinopoiskClient, media_type: str) -> dict[int, str]:
    return await get_genres(client, media_type)


@app.command("search")
def search_cmd(
    query: str = typer.Argument(
        ...,
        help=(
            "Поисковый запрос — название фильма, сериала или ключевые слова. "
            "Поддерживается русский и английский. Пример: 'Интерстеллар' или 'Interstellar'"
        ),
    ),
    content_type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help=(
            "Фильтр по типу контента:\n"
            "  movie — только фильмы\n"
            "  tv    — только сериалы\n"
            "  (без флага — искать всё)"
        ),
    ),
    year: Optional[str] = typer.Option(
        None, "--year", "-y",
        help="Год выхода. Пример: --year 2010",
    ),
    lang: Optional[str] = typer.Option(
        None, "--lang",
        help="Язык результатов: ru (по умолчанию) | en. Пример: --lang en",
    ),
    page: int = typer.Option(
        1, "--page", "-p",
        help="Страница результатов (по 10 на странице). Пример: --page 2",
    ),
    sort: Optional[str] = typer.Option(
        None, "--sort", "-s",
        help="Сортировка: relevance (по релевантности, по умолч.) | rating | year",
    ),
    output: str = typer.Option(
        "table", "--output", "-o",
        help="Формат вывода: table (таблица) | json | csv",
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache",
        help="Игнорировать кэш и запросить свежие данные с сервера",
    ),
) -> None:
    """🔍 Поиск фильмов и сериалов через Кинопоиск.

    Ищет по названию (русском или английском) в базе Кинопоиска.
    Результаты кэшируются на 1 час для ускорения повторных запросов.

    Примеры:
      movie-tracker-claude search 'Интерстеллар'
      movie-tracker-claude search 'Во все тяжкие' --type tv
      movie-tracker-claude search 'Нолан' --type movie --sort rating
      movie-tracker-claude search 'Начало' --year 2010
      movie-tracker-claude search 'Breaking Bad' --page 2
      movie-tracker-claude search 'фантастика' --output json
    """
    api_key = get_api_key()
    if not api_key:
        error("API ключ не установлен. Выполните: movie-tracker-claude auth token YOUR_KEY")
        raise typer.Exit(1)

    if content_type and content_type not in ("movie", "tv", "all"):
        error("Тип должен быть: movie, tv или не указывать совсем")
        raise typer.Exit(1)

    language = lang or get_language()
    validated_year = validate_year(year)
    page = validate_page(page)

    async def _run() -> None:
        cache_key = make_search_key(query, type=content_type, year=validated_year, page=page)
        if not no_cache:
            cached = cache_get(cache_key)
            if cached:
                print_search_results(cached, output_format=output)
                info("[dim](из кэша)[/dim]")
                return

        async with KinopoiskClient(api_key=api_key) as client:
            if content_type == "movie":
                result = await search_movies(client, query, page=page, year=validated_year, language=language)
            elif content_type == "tv":
                result = await search_tv(client, query, page=page, year=validated_year, language=language)
            else:
                result = await search_multi(client, query, page=page, language=language)

            cache_set(cache_key, result, TTL_SEARCH)

        if not result.results:
            info("Ничего не найдено. Попробуйте изменить запрос или убрать фильтры.")
            return

        print_search_results(result, output_format=output)
        if result.total_pages > 1:
            info(
                f"Страница {page} из {result.total_pages} "
                f"(всего {result.total_results}). "
                f"Следующая: [bold]movie-tracker-claude search '{query}' --page {page + 1}[/bold]"
            )

    try:
        asyncio.run(_run())
    except MovieTrackerError as e:
        error(e.message)
        raise typer.Exit(e.exit_code)
