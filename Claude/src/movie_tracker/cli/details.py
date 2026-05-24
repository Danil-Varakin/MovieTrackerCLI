"""CLI команда: details — детальная информация о фильме или сериале."""

from __future__ import annotations

import asyncio
from typing import Optional

import typer

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.details import (
    get_movie_credits,
    get_movie_details,
    get_movie_reviews,
    get_movie_similar as get_similar_movies,
    get_tv_similar as get_similar_tv,
    get_tv_credits,
    get_tv_details,
    get_movie_reviews as get_tv_reviews,
)
from movie_tracker.cache.manager import TTL_DETAILS, cache_get, cache_set, make_details_key
from movie_tracker.config import get_api_key, get_language
from movie_tracker.exceptions import MovieTrackerError
from movie_tracker.formatters.table import (
    error,
    info,
    print_credits,
    print_movie_details,
    print_tv_details,
    print_reviews,
    print_search_results,
    success,
)
from movie_tracker.models import SearchPage, SearchResult

app = typer.Typer()


async def _auto_detect_type(client: KinopoiskClient, film_id: int) -> str:
    """Определяет тип контента по ID через /api/v2.2/films/{id}."""
    try:
        await get_movie_details(client, film_id)
        return "movie"
    except Exception:
        pass
    try:
        await get_tv_details(client, film_id)
        return "tv"
    except Exception:
        pass
    raise MovieTrackerError(f"Контент с ID {film_id} не найден (проверьте тип: --type movie/tv)")


async def _run_details(
    film_id: int,
    content_type: Optional[str],
    section: str,
    lang: Optional[str],
    reviews_page: int,
) -> None:
    api_key = get_api_key()
    if not api_key:
        raise MovieTrackerError("API ключ не установлен.")

    language = lang or get_language()

    async with KinopoiskClient(api_key=api_key) as client:
        if not content_type or content_type == "auto":
            content_type = await _auto_detect_type(client, film_id)

        cache_key = make_details_key(film_id, content_type, section=section, lang=language)
        cached = cache_get(cache_key)

        if cached:
            # Выводим из кэша
            _render_cached(cached, section)
            info("[dim](из кэша)[/dim]")
            return

        result: dict = {}

        if section in ("info", "all"):
            info_key = make_details_key(film_id, content_type, section="info", lang=language)
            info_cached = cache_get(info_key)
            if info_cached:
                details_data = info_cached
            else:
                if content_type == "movie":
                    details_data = await get_movie_details(client, film_id)
                else:
                    details_data = await get_tv_details(client, film_id)
                cache_set(info_key, details_data, TTL_DETAILS)
            result["info"] = details_data
            print_movie_details(details_data) if content_type == "movie" else print_tv_details(details_data)

        if section in ("cast", "all"):
            if content_type == "movie":
                credits = await get_movie_credits(client, film_id)
            else:
                credits = await get_tv_credits(client, film_id)
            result["cast"] = credits
            print_credits(credits)

        if section in ("reviews", "all"):
            if content_type == "movie":
                reviews_data = await get_movie_reviews(client, film_id, reviews_page)
            else:
                reviews_data = await get_tv_reviews(client, film_id, reviews_page)
            result["reviews"] = reviews_data
            print_reviews(reviews_data.get("results",[]), reviews_page, reviews_data.get("total_pages",1))

        if section in ("similar", "all"):
            if content_type == "movie":
                similar = await get_similar_movies(client, film_id)
            else:
                similar = await get_similar_tv(client, film_id)
            result["similar"] = similar
            items = [SearchResult.from_api(r) for r in similar.get("results", [])]
            if items:
                info(f"\n[bold]Похожие ({len(items)}):[/bold]")
                page = SearchPage(page=1, total_pages=1, total_results=len(items), results=items)
                print_search_results(page)

        if section != "all":
            cache_set(cache_key, result, TTL_DETAILS)


def _render_cached(cached: dict, section: str) -> None:
    """Рендеринг кэшированных данных."""
    from movie_tracker.formatters.table import print_movie_details, print_tv_details, print_credits, print_reviews, print_search_results
    from movie_tracker.models import SearchPage, SearchResult
    if "info" in cached and section in ("info", "all"):
        print_movie_details(cached["info"])
    if "cast" in cached and section in ("cast", "all"):
        print_credits(cached["cast"])
    if "reviews" in cached and section in ("reviews", "all"):
        print_reviews(cached["reviews"].get("results",[]), 1, 1)
    if "similar" in cached and section in ("similar", "all"):
        items = [SearchResult.from_api(r) for r in cached["similar"].get("results", [])]
        if items:
            page = SearchPage(page=1, total_pages=1, total_results=len(items), results=items)
            print_search_results(page)


@app.command("details")
def details_cmd(
    film_id: int = typer.Argument(
        ...,
        help=(
            "ID фильма или сериала на Кинопоиске. "
            "Узнать ID: movie-tracker-claude search <название> → колонка ID"
        ),
    ),
    content_type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help=(
            "Тип контента:\n"
            "  movie — фильм\n"
            "  tv    — сериал\n"
            "  (без флага — определяется автоматически)"
        ),
    ),
    section: str = typer.Option(
        "all", "--section", "-s",
        help=(
            "Какой раздел показать:\n"
            "  all      — всё (по умолчанию)\n"
            "  info     — основная информация\n"
            "  cast     — актёры и съёмочная группа\n"
            "  reviews  — рецензии зрителей\n"
            "  similar  — похожие фильмы/сериалы"
        ),
    ),
    lang: Optional[str] = typer.Option(
        None, "--lang",
        help="Язык описания: ru | en",
    ),
    reviews_page: int = typer.Option(
        1, "--reviews-page",
        help="Страница рецензий (по 20 на странице). Пример: --reviews-page 2",
    ),
) -> None:
    """📄 Подробная информация о фильме или сериале.

    Показывает детали по ID Кинопоиска:
    рейтинг, жанр, год, страна, актёры, рецензии и похожие.

    Сначала найдите ID: movie-tracker-claude search 'название'

    Примеры:
      movie-tracker-claude details 447301                    # вся информация
      movie-tracker-claude details 447301 --type movie       # явно указать тип
      movie-tracker-claude details 447301 --section info     # только основное
      movie-tracker-claude details 447301 --section cast     # только актёры
      movie-tracker-claude details 447301 --section reviews  # только рецензии
      movie-tracker-claude details 447301 --section similar  # похожие фильмы
      movie-tracker-claude details 447301 --reviews-page 2   # вторая страница рецензий
    """
    if section not in ("info", "cast", "reviews", "similar", "all"):
        error("Раздел должен быть: info | cast | reviews | similar | all")
        raise typer.Exit(1)

    if content_type and content_type not in ("movie", "tv"):
        error("Тип должен быть: movie | tv")
        raise typer.Exit(1)

    try:
        asyncio.run(_run_details(film_id, content_type, section, lang, reviews_page))
    except MovieTrackerError as e:
        error(e.message)
        raise typer.Exit(e.exit_code)
