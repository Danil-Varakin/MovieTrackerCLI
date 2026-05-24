from __future__ import annotations

from typing import Any

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.models.movie import MediaItem

DETAILS_TTL = 24 * 3600


def fetch_details(
    client: KinopoiskClient,
    item_id: int,
    *,
    section: str = "all",
    reviews_page: int = 1,
) -> dict[str, Any]:
    details_payload = client.get(
        f"/v2.2/films/{item_id}",
        ttl_seconds=DETAILS_TTL,
        cache_namespace="details",
    )
    assert isinstance(details_payload, dict)
    result: dict[str, Any] = {
        "info": MediaItem.from_api(details_payload).to_dict(),
        "raw": details_payload,
    }

    if section in {"all", "cast"}:
        staff_payload = client.get(
            "/v1/staff",
            params={"filmId": item_id},
            ttl_seconds=DETAILS_TTL,
            cache_namespace="staff",
        )
        result["staff"] = staff_payload if isinstance(staff_payload, list) else []

    if section in {"all", "reviews"}:
        reviews_payload = client.get(
            f"/v2.2/films/{item_id}/reviews",
            params={"page": reviews_page, "order": "DATE_DESC"},
            ttl_seconds=DETAILS_TTL,
            cache_namespace="reviews",
        )
        result["reviews"] = (
            reviews_payload.get("items", []) if isinstance(reviews_payload, dict) else []
        )

    if section in {"all", "similar"}:
        similar_payload = client.get(
            f"/v2.2/films/{item_id}/similars",
            ttl_seconds=12 * 3600,
            cache_namespace="similar",
        )
        if isinstance(similar_payload, dict):
            result["similar"] = [
                MediaItem.from_api(item).to_dict() for item in similar_payload.get("items", [])
            ]
        else:
            result["similar"] = []

    if section == "all" and details_payload.get("serial"):
        seasons_payload = client.get(
            f"/v2.2/films/{item_id}/seasons",
            ttl_seconds=DETAILS_TTL,
            cache_namespace="seasons",
        )
        result["seasons"] = (
            seasons_payload.get("items", []) if isinstance(seasons_payload, dict) else []
        )

    return result
