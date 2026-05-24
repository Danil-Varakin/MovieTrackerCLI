"""Кинопоиск Unofficial API — поиск фильмов и сериалов.

Документация: https://kinopoiskapiunofficial.tech/documentation
Все пути: /api/v2.2/films?keyword=...&type=...&page=...
Заголовок: X-API-KEY: <token>
"""

from __future__ import annotations

from typing import Optional

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.models import SearchPage, SearchResult

_TYPE_MAP = {
    "FILM": "movie", "VIDEO": "movie", "MINI_SERIES": "tv",
    "TV_SERIES": "tv", "TV_SHOW": "tv", "UNKNOWN": "movie",
}


def _normalize(item: dict) -> dict:
    kp_type = item.get("type", item.get("filmType", "FILM"))
    media_type = _TYPE_MAP.get(kp_type, "movie")
    try:
        rating = float(str(item.get("rating") or item.get("ratingKinopoisk") or 0).replace(",", "."))
    except (ValueError, TypeError):
        rating = 0.0
    year = str(item.get("year", "—")) if item.get("year") else "—"
    genres = [g["genre"] for g in item.get("genres", []) if g.get("genre")]
    return {
        "id": item.get("kinopoiskId") or item.get("filmId") or 0,
        "media_type": media_type,
        "title": item.get("nameRu") or item.get("nameEn") or item.get("nameOriginal") or "—",
        "original_title": item.get("nameOriginal") or item.get("nameEn") or "—",
        "overview": item.get("description", ""),
        "release_date": f"{year}-01-01" if year != "—" else "",
        "genre_ids": [],
        "genre_names": genres,
        "vote_average": rating,
        "vote_count": item.get("ratingVoteCount", 0),
        "popularity": rating,
    }


def _make_page(data: dict, page: int) -> SearchPage:
    items = [_normalize(i) for i in data.get("items", [])]
    return SearchPage(
        page=page,
        total_pages=data.get("totalPages", 1),
        total_results=data.get("total", len(items)),
        results=[SearchResult.from_api(i) for i in items],
    )


async def search_multi(client: KinopoiskClient, query: str, page: int = 1, language: Optional[str] = None) -> SearchPage:
    """GET /api/v2.2/films?keyword=...&type=ALL&page=..."""
    data = await client.get("/api/v2.2/films", keyword=query, type="ALL", page=page)
    return _make_page(data, page)


async def search_movies(client: KinopoiskClient, query: str, page: int = 1, year: Optional[str] = None, language: Optional[str] = None) -> SearchPage:
    """GET /api/v2.2/films?keyword=...&type=FILM&page=..."""
    params: dict = {"keyword": query, "type": "FILM", "page": page}
    if year:
        params["yearFrom"] = year
        params["yearTo"] = year
    data = await client.get("/api/v2.2/films", **params)
    return _make_page(data, page)


async def search_tv(client: KinopoiskClient, query: str, page: int = 1, year: Optional[str] = None, language: Optional[str] = None) -> SearchPage:
    """GET /api/v2.2/films?keyword=...&type=TV_SERIES&page=..."""
    params: dict = {"keyword": query, "type": "TV_SERIES", "page": page}
    if year:
        params["yearFrom"] = year
        params["yearTo"] = year
    data = await client.get("/api/v2.2/films", **params)
    return _make_page(data, page)


async def discover_movies(client: KinopoiskClient, genre_ids: Optional[str] = None, sort_by: str = "NUM_VOTE", page: int = 1, year: Optional[str] = None, language: Optional[str] = None) -> SearchPage:
    """GET /api/v2.2/films?type=FILM&page=..."""
    params: dict = {"type": "FILM", "page": page}
    if year:
        params["yearFrom"] = year
        params["yearTo"] = year
    data = await client.get("/api/v2.2/films", **params)
    return _make_page(data, page)


async def discover_tv(client: KinopoiskClient, genre_ids: Optional[str] = None, sort_by: str = "NUM_VOTE", page: int = 1, year: Optional[str] = None, language: Optional[str] = None) -> SearchPage:
    """GET /api/v2.2/films?type=TV_SERIES&page=..."""
    params: dict = {"type": "TV_SERIES", "page": page}
    if year:
        params["yearFrom"] = year
        params["yearTo"] = year
    data = await client.get("/api/v2.2/films", **params)
    return _make_page(data, page)


async def get_genres(client: KinopoiskClient, media_type: str = "movie") -> dict[int, str]:
    """Жанры в Кинопоиске — текстовые, не числовые."""
    return {}
