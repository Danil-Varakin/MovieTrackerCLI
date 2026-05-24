from __future__ import annotations

from typing import Any

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.models.movie import MediaItem


def trending_media(
    client: KinopoiskClient,
    *,
    content_type: str = "all",
    window: str = "day",
    page: int = 1,
    limit: int = 20,
) -> list[dict[str, Any]]:
    top_type = "TOP_AWAIT_FILMS" if window == "day" else "TOP_100_POPULAR_FILMS"
    payload = client.get(
        "/v2.2/films/top",
        params={"type": top_type, "page": page},
        ttl_seconds=1800 if window == "day" else 3 * 3600,
        cache_namespace="trending",
    )
    raw_items = payload.get("films", []) if isinstance(payload, dict) else []
    items = [
        MediaItem.from_api(item)
        for item in raw_items
        if item.get("kinopoiskId") or item.get("filmId")
    ]
    if content_type != "all":
        items = [item for item in items if item.media_type == content_type]
    return [item.to_dict() for item in items[:limit]]
