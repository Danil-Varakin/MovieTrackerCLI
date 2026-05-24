from __future__ import annotations

from collections import Counter
from typing import Any

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.search import resolve_genre_id
from movie_tracker.models.movie import MediaItem
from movie_tracker.storage.watchlist import WatchlistStore
from movie_tracker.utils.helpers import to_kinopoisk_type


def recommend_by_id(
    client: KinopoiskClient, item_id: int, *, limit: int = 10
) -> list[dict[str, Any]]:
    payload = client.get(
        f"/v2.2/films/{item_id}/similars",
        ttl_seconds=12 * 3600,
        cache_namespace="recommendations",
    )
    raw_items = payload.get("items", []) if isinstance(payload, dict) else []
    return [MediaItem.from_api(item).to_dict() for item in raw_items[:limit]]


def recommend_by_profile(
    client: KinopoiskClient,
    store: WatchlistStore,
    *,
    content_type: str = "all",
    genres: list[str] | None = None,
    exclude_watched: bool = False,
    limit: int = 10,
    page: int = 1,
) -> list[dict[str, Any]]:
    genre_ids: list[int] = []
    if genres:
        genre_ids = [
            genre_id
            for genre_id in (resolve_genre_id(client, genre) for genre in genres)
            if genre_id
        ]
    else:
        rows = store.list()
        genre_counter = Counter(genre for row in rows for genre in row.get("genres", []))
        for genre, _count in genre_counter.most_common(3):
            genre_id = resolve_genre_id(client, genre)
            if genre_id:
                genre_ids.append(genre_id)

    params: dict[str, Any] = {
        "type": to_kinopoisk_type(content_type),
        "order": "RATING",
        "page": page,
        "genres": ",".join(str(genre_id) for genre_id in genre_ids) if genre_ids else None,
        "ratingFrom": 6,
        "ratingTo": 10,
    }
    payload = client.get(
        "/v2.2/films",
        params=params,
        ttl_seconds=12 * 3600,
        cache_namespace="recommendations",
    )
    raw_items = payload.get("items", []) if isinstance(payload, dict) else []
    watched_ids = (
        {row["id"] for row in store.list(status="watched") if row.get("id") is not None}
        if exclude_watched
        else set()
    )

    items = [
        MediaItem.from_api(item)
        for item in raw_items
        if item.get("kinopoiskId") or item.get("filmId")
    ]
    if exclude_watched:
        items = [item for item in items if item.id not in watched_ids]
    return [item.to_dict() for item in items[:limit]]
