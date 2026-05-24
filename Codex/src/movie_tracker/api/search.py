from __future__ import annotations

from typing import Any

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.exceptions import MovieTrackerError
from movie_tracker.models.movie import MediaItem
from movie_tracker.utils.helpers import genre_lookup_key, to_kinopoisk_type

FILTERS_TTL = 7 * 24 * 3600
SEARCH_TTL = 3600


def get_filters(client: KinopoiskClient) -> dict[str, Any]:
    payload = client.get("/v2.2/films/filters", ttl_seconds=FILTERS_TTL, cache_namespace="filters")
    return payload if isinstance(payload, dict) else {}


def resolve_genre_id(client: KinopoiskClient, genre: str | None) -> int | None:
    if not genre:
        return None
    value = genre.strip()
    if value.isdigit():
        return int(value)
    lookup = genre_lookup_key(value)
    filters = get_filters(client)
    for item in filters.get("genres", []):
        if str(item.get("genre", "")).lower() == lookup:
            return int(item["id"])
    raise MovieTrackerError(f"Жанр '{genre}' не найден в справочнике Kinopoisk API.")


def _normalize_collection(payload: dict[str, Any] | list[dict[str, Any]]) -> list[MediaItem]:
    if isinstance(payload, list):
        raw_items = payload
    else:
        raw_items = payload.get("items") or payload.get("films") or payload.get("results") or []
    return [
        MediaItem.from_api(item)
        for item in raw_items
        if item.get("kinopoiskId") or item.get("filmId")
    ]


def _sort_items(items: list[MediaItem], sort: str) -> list[MediaItem]:
    if sort == "rating":
        return sorted(items, key=lambda item: float(item.rating or 0), reverse=True)
    if sort == "year":
        return sorted(items, key=lambda item: int(item.year or 0), reverse=True)
    if sort == "popularity":
        return sorted(items, key=lambda item: item.votes or 0, reverse=True)
    return items


def search_media(
    client: KinopoiskClient,
    *,
    query: str,
    content_type: str = "all",
    genre: str | None = None,
    year: int | None = None,
    page: int = 1,
    per_page: int = 10,
    sort: str = "relevance",
) -> list[dict[str, Any]]:
    genre_id = resolve_genre_id(client, genre)
    use_filters = bool(genre_id or year or sort != "relevance" or not query.strip())

    if use_filters:
        params: dict[str, Any] = {
            "type": to_kinopoisk_type(content_type),
            "order": {"rating": "RATING", "popularity": "NUM_VOTE", "year": "YEAR"}.get(
                sort, "RATING"
            ),
            "page": page,
            "keyword": query.strip() or None,
            "genres": genre_id,
            "yearFrom": year,
            "yearTo": year,
            "ratingFrom": 0,
            "ratingTo": 10,
        }
        payload = client.get(
            "/v2.2/films",
            params=params,
            ttl_seconds=SEARCH_TTL,
            cache_namespace="search",
        )
    else:
        payload = client.get(
            "/v2.1/films/search-by-keyword",
            params={"keyword": query.strip(), "page": page},
            ttl_seconds=SEARCH_TTL,
            cache_namespace="search",
        )

    items = _sort_items(_normalize_collection(payload), sort)
    if content_type != "all":
        items = [item for item in items if item.media_type == content_type]
    return [item.to_dict() for item in items[:per_page]]
