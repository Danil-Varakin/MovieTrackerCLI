"""CLI команды: rate, popular, trending, recommend."""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.details import get_movie_similar
from movie_tracker.api.search import discover_movies, discover_tv
from movie_tracker.cache.manager import (
    TTL_POPULAR,
    TTL_RECOMMEND,
    TTL_TRENDING_DAY,
    TTL_TRENDING_WEEK,
    cache_get,
    cache_set,
    make_popular_key,
    make_recommend_key,
    make_trending_key,
)
from movie_tracker.config import get_api_key
from movie_tracker.exceptions import MovieTrackerError
from movie_tracker.formatters.table import (
    error,
    info,
    print_search_results,
    success,
    warning,
)
from movie_tracker.models import SearchPage, SearchResult
from movie_tracker.storage import watchlist as wl_storage
from movie_tracker.utils.validators import validate_rating

rate_app = typer.Typer()
popular_app = typer.Typer()
trending_app = typer.Typer()
recommend_app = typer.Typer()

_console = Console()

# ─────────────────────────────────────────────────────────────
# Rate
# ─────────────────────────────────────────────────────────────


@rate_app.command("rate")
def rate_cmd(
    film_id: int = typer.Argument(
        ...,
        help="ID фильма или сериала (Кинопоиск). Узнать ID: movie-tracker-claude search <название>",
    ),
    rating: float = typer.Argument(
        ...,
        help="Оценка от 0.5 до 10.0 (шаг 0.5). Пример: 8.5",
    ),
    content_type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="Тип контента: movie (фильм) | tv (сериал). Необязательно.",
    ),
    review: Optional[str] = typer.Option(
        None, "--review", "-r",
        help="Добавить личный текстовый отзыв. Пример: --review 'Шедевр Нолана'",
    ),
) -> None:
    """⭐ Оценить фильм или сериал.

    Оценка сохраняется локально в вашем watchlist.
    Запись с таким ID должна уже существовать в списке.

    Примеры:
      movie-tracker-claude rate 447301 9.5
      movie-tracker-claude rate 447301 8.0 --review 'Блестящая режиссура'
    """
    try:
        validated = validate_rating(rating)
    except MovieTrackerError as e:
        error(e.message)
        raise typer.Exit(1)

    entry = wl_storage.get_entry(film_id)
    if entry:
        wl_storage.update_entry(film_id, rating=validated, status="watched")
        if review:
            wl_storage.update_entry(film_id, note=review)
        success(f"Оценка [bold]{validated}[/bold] сохранена для «{entry.title}»")
        if review:
            info(f"Отзыв: {review}")
    else:
        warning(f"ID {film_id} не найден в watchlist. Сначала добавьте:")
        info(f"  movie-tracker-claude add-watchlist {film_id}")


# ─────────────────────────────────────────────────────────────
# Popular — автофetch всех страниц до --limit
# ─────────────────────────────────────────────────────────────


@popular_app.command("popular")
def popular_cmd(
    content_type: str = typer.Option(
        "movie", "--type", "-t",
        help="Тип контента: movie (фильмы) | tv (сериалы)",
    ),
    limit: int = typer.Option(
        20, "--limit", "-l",
        help="Сколько позиций показать (1–200). По умолчанию: 20",
    ),
    output: str = typer.Option(
        "table", "--output", "-o",
        help="Формат вывода: table (таблица) | json | csv",
    ),
) -> None:
    """🔥 Популярные фильмы и сериалы — Топ Кинопоиска.

    Загружает актуальный рейтинг популярности с Кинопоиска.
    Используйте --limit чтобы получить нужное количество позиций.

    Примеры:
      movie-tracker-claude popular                     # топ-20 фильмов
      movie-tracker-claude popular --type tv           # топ-20 сериалов
      movie-tracker-claude popular --limit 50          # топ-50 фильмов
      movie-tracker-claude popular --output json       # вывод в JSON
    """
    if content_type not in ("movie", "tv"):
        error("Тип должен быть: movie (фильмы) или tv (сериалы)")
        raise typer.Exit(1)

    limit = max(1, min(limit, 200))
    api_key = get_api_key()
    if not api_key:
        error("API ключ не установлен. Выполните: movie-tracker-claude auth token YOUR_KEY")
        raise typer.Exit(1)

    async def _fetch() -> None:
        kp_type = "TOP_100_POPULAR_FILMS" if content_type == "movie" else "TOP_TV_SHOWS"
        all_items: list[SearchResult] = []
        page = 1

        async with KinopoiskClient(api_key=api_key) as client:
            while len(all_items) < limit:
                cache_key = make_popular_key(content_type, page)
                cached = cache_get(cache_key)

                if cached:
                    page_items = cached.results
                    total_pages = cached.total_pages
                else:
                    data = await client.get("/api/v2.2/films/top", type=kp_type, page=page)
                    total_pages = data.get("pagesCount", 1)
                    page_items = []
                    for item in data.get("films", []):
                        r_val = item.get("rating", "0") or "0"
                        try:
                            rf = float(str(r_val).replace(",", "."))
                        except (ValueError, TypeError):
                            rf = 0.0
                        genres = [g["genre"] for g in item.get("genres", []) if g.get("genre")]
                        page_items.append(SearchResult(
                            id=item.get("filmId", 0),
                            media_type=content_type,
                            title=item.get("nameRu") or item.get("nameEn") or "—",
                            original_title=item.get("nameEn") or "—",
                            overview="",
                            year=str(item.get("year", "—")),
                            vote_average=rf,
                            genre_names_str=", ".join(genres[:3]),
                        ))
                    fake_page_obj = SearchPage(page=page, total_pages=total_pages, total_results=len(page_items), results=page_items)
                    cache_set(cache_key, fake_page_obj, TTL_POPULAR)

                all_items.extend(page_items)
                if page >= total_pages:
                    break
                page += 1

        result = SearchPage(
            page=1,
            total_pages=1,
            total_results=len(all_items[:limit]),
            results=all_items[:limit],
        )
        label = "Топ фильмов Кинопоиска" if content_type == "movie" else "Топ сериалов Кинопоиска"
        _console.print(f"\n[bold]🔥 {label} (топ-{limit})[/bold]")
        print_search_results(result, output_format=output)

    try:
        asyncio.run(_fetch())
    except MovieTrackerError as e:
        error(e.message)
        raise typer.Exit(e.exit_code)


# ─────────────────────────────────────────────────────────────
# Trending — автофetch всех страниц до --limit
# ─────────────────────────────────────────────────────────────


@trending_app.command("trending")
def trending_cmd(
    content_type: str = typer.Option(
        "movie", "--type", "-t",
        help="Тип контента: movie (фильмы) | tv (сериалы)",
    ),
    window: str = typer.Option(
        "popular", "--window", "-w",
        help=(
            "Список для отображения:\n"
            "  popular  — популярное прямо сейчас (Топ-100)\n"
            "  top250   — классика всех времён (Топ-250)"
        ),
    ),
    limit: int = typer.Option(
        20, "--limit", "-l",
        help="Сколько позиций показать (1–250). По умолчанию: 20",
    ),
    output: str = typer.Option(
        "table", "--output", "-o",
        help="Формат вывода: table (таблица) | json | csv",
    ),
) -> None:
    """📈 Популярный и легендарный контент — рейтинги Кинопоиска.

    Два режима через --window:
      popular  — что смотрят прямо сейчас (обновляется часто)
      top250   — Топ-250 лучших фильмов всех времён по версии КП

    Примеры:
      movie-tracker-claude trending                          # топ-20 популярных фильмов
      movie-tracker-claude trending --window top250          # топ-20 из Топ-250
      movie-tracker-claude trending --window top250 --limit 250   # полный Топ-250
      movie-tracker-claude trending --type tv --limit 50     # топ-50 популярных сериалов
      movie-tracker-claude trending --output json            # вывод в JSON
    """
    if content_type not in ("movie", "tv"):
        error("Тип должен быть: movie (фильмы) или tv (сериалы)")
        raise typer.Exit(1)
    if window not in ("popular", "top250"):
        error("Режим должен быть: popular (популярное) или top250 (Топ-250)")
        raise typer.Exit(1)

    limit = max(1, min(limit, 250))
    api_key = get_api_key()
    if not api_key:
        error("API ключ не установлен.")
        raise typer.Exit(1)

    ttl = TTL_TRENDING_DAY if window == "popular" else TTL_TRENDING_WEEK

    async def _fetch() -> None:
        if content_type == "movie":
            kp_type = "TOP_250_BEST_FILMS" if window == "top250" else "TOP_100_POPULAR_FILMS"
        else:
            kp_type = "TOP_TV_SHOWS"

        all_items: list[SearchResult] = []
        page = 1

        async with KinopoiskClient(api_key=api_key) as client:
            while len(all_items) < limit:
                cache_key = make_trending_key(content_type, window, page)
                cached = cache_get(cache_key)

                if cached:
                    page_items = cached.results
                    total_pages = cached.total_pages
                else:
                    data = await client.get("/api/v2.2/films/top", type=kp_type, page=page)
                    total_pages = data.get("pagesCount", 1)
                    page_items = []
                    for item in data.get("films", []):
                        r_val = item.get("rating", "0") or "0"
                        try:
                            rf = float(str(r_val).replace(",", "."))
                        except (ValueError, TypeError):
                            rf = 0.0
                        genres = [g["genre"] for g in item.get("genres", []) if g.get("genre")]
                        page_items.append(SearchResult(
                            id=item.get("filmId", 0),
                            media_type=content_type,
                            title=item.get("nameRu") or item.get("nameEn") or "—",
                            original_title=item.get("nameEn") or "—",
                            overview="",
                            year=str(item.get("year", "—")),
                            vote_average=rf,
                            genre_names_str=", ".join(genres[:3]),
                        ))
                    fake_page_obj = SearchPage(page=page, total_pages=total_pages, total_results=len(page_items), results=page_items)
                    cache_set(cache_key, fake_page_obj, ttl)

                all_items.extend(page_items)
                if page >= total_pages:
                    break
                page += 1

        result = SearchPage(
            page=1, total_pages=1,
            total_results=len(all_items[:limit]),
            results=all_items[:limit],
        )
        if window == "top250":
            label = f"Топ-250 лучших фильмов всех времён (показано {len(all_items[:limit])})"
        else:
            label = f"Популярные {'фильмы' if content_type == 'movie' else 'сериалы'} прямо сейчас"

        _console.print(f"\n[bold]📈 {label}[/bold]")
        print_search_results(result, output_format=output)

    try:
        asyncio.run(_fetch())
    except MovieTrackerError as e:
        error(e.message)
        raise typer.Exit(e.exit_code)


# ─────────────────────────────────────────────────────────────
# Recommend — без пагинации
# ─────────────────────────────────────────────────────────────


@recommend_app.command("recommend")
def recommend_cmd(
    based_on: Optional[int] = typer.Option(
        None, "--based-on", "-b",
        help=(
            "ID фильма/сериала для поиска похожих. "
            "Пример: --based-on 447301 (Начало)"
        ),
    ),
    content_type: str = typer.Option(
        "movie", "--type", "-t",
        help="Тип контента при поиске без --based-on: movie | tv",
    ),
    exclude_watched: bool = typer.Option(
        False, "--exclude-watched", "-e",
        help="Исключить из результатов фильмы/сериалы, уже помеченные как просмотренные",
    ),
    limit: int = typer.Option(
        10, "--limit", "-l",
        help="Сколько рекомендаций показать (1–40). По умолчанию: 10",
    ),
) -> None:
    """🎯 Рекомендации на основе фильма или вашего watchlist.

    Два режима работы:

    1. По конкретному фильму (--based-on):
       Находит похожие фильмы/сериалы по базе Кинопоиска.

    2. Без --based-on:
       Показывает популярный контент указанного типа.

    Примеры:
      movie-tracker-claude recommend --based-on 447301          # похожие на "Начало"
      movie-tracker-claude recommend --based-on 447301 --limit 20
      movie-tracker-claude recommend --exclude-watched          # только непросмотренное
      movie-tracker-claude recommend --type tv --limit 15       # популярные сериалы
    """
    api_key = get_api_key()
    if not api_key:
        error("API ключ не установлен.")
        raise typer.Exit(1)

    limit = max(1, min(limit, 40))
    watched_ids = wl_storage.get_watched_ids() if exclude_watched else set()

    async def _fetch() -> None:
        async with KinopoiskClient(api_key=api_key) as client:
            results: list[SearchResult] = []

            if based_on:
                cache_key = make_recommend_key(based_on, content_type, 1)
                cached = cache_get(cache_key)
                if cached:
                    data = cached
                else:
                    data = await get_movie_similar(client, based_on)
                    cache_set(cache_key, data, TTL_RECOMMEND)
                results = [SearchResult.from_api(r) for r in data.get("results", [])]
            else:
                # Популярный контент как fallback
                kp_type = "TOP_100_POPULAR_FILMS" if content_type == "movie" else "TOP_TV_SHOWS"
                data = await client.get("/api/v2.2/films/top", type=kp_type, page=1)
                for item in data.get("films", []):
                    r_val = item.get("rating", "0") or "0"
                    try:
                        rv = float(str(r_val).replace(",", "."))
                    except Exception:
                        rv = 0.0
                    genres = [g["genre"] for g in item.get("genres", []) if g.get("genre")]
                    results.append(SearchResult(
                        id=item.get("filmId", 0),
                        media_type=content_type,
                        title=item.get("nameRu") or item.get("nameEn") or "—",
                        original_title=item.get("nameEn") or "—",
                        overview="",
                        year=str(item.get("year", "—")),
                        vote_average=rv,
                        genre_names_str=", ".join(genres[:3]),
                    ))

            if exclude_watched:
                results = [r for r in results if r.id not in watched_ids]

            results = results[:limit]

            if not results:
                _console.print("[yellow]Нет рекомендаций по текущим критериям.[/yellow]")
                return

            label = (
                f"Похожие на ID {based_on}" if based_on
                else f"Рекомендованные {'фильмы' if content_type == 'movie' else 'сериалы'}"
            )
            _console.print(f"\n[bold]🎯 {label} (топ-{len(results)})[/bold]")
            fake_page = SearchPage(page=1, total_pages=1, total_results=len(results), results=results)
            print_search_results(fake_page)

    try:
        asyncio.run(_fetch())
    except MovieTrackerError as e:
        error(e.message)
        raise typer.Exit(e.exit_code)
