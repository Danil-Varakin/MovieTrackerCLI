from __future__ import annotations

from typing import Any

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.models.movie import MediaItem


def popular_media(
    client: KinopoiskClient,
    *,
    content_type: str = "movie",
    page: int = 1,
    limit: int = 20,
) -> list[dict[str, Any]]:
    if content_type == "tv":
        payload = client.get(
            "/v2.2/films",
            params={
                "type": "TV_SERIES",
                "order": "NUM_VOTE",
                "page": page,
                "ratingFrom": 0,
                "ratingTo": 10,
            },
            ttl_seconds=3 * 3600,
            cache_namespace="popular",
        )
        raw_items = payload.get("items", []) if isinstance(payload, dict) else []
    else:
        payload = client.get(
            "/v2.2/films/top",
            params={"type": "TOP_100_POPULAR_FILMS", "page": page},
            ttl_seconds=3 * 3600,
            cache_namespace="popular",
        )
        raw_items = payload.get("films", []) if isinstance(payload, dict) else []

    return [MediaItem.from_api(item).to_dict() for item in raw_items[:limit]]
