"""Кинопоиск Unofficial API — детали, состав, рецензии, похожие.

Все пути: /api/v2.2/films/{id}, /api/v1/staff, /api/v1/reviews
"""

from __future__ import annotations

from typing import Optional

from movie_tracker.api.client import KinopoiskClient


async def get_movie_details(client: KinopoiskClient, film_id: int) -> dict:
    """GET /api/v2.2/films/{id}"""
    return await client.get(f"/api/v2.2/films/{film_id}")


async def get_tv_details(client: KinopoiskClient, film_id: int) -> dict:
    """GET /api/v2.2/films/{id} — тот же эндпоинт для сериалов."""
    return await client.get(f"/api/v2.2/films/{film_id}")


async def get_movie_credits(client: KinopoiskClient, film_id: int) -> dict:
    """GET /api/v1/staff?filmId={id}"""
    staff = await client.get("/api/v1/staff", filmId=film_id)
    cast, crew = [], []
    for person in (staff if isinstance(staff, list) else []):
        name = person.get("nameRu") or person.get("nameEn") or "—"
        prof_key = person.get("professionKey", "")
        entry = {
            "id": person.get("staffId", 0),
            "name": name,
            "character": person.get("description", ""),
            "order": person.get("order", 99),
            "job": person.get("professionText", ""),
            "department": prof_key,
        }
        if prof_key == "ACTOR":
            cast.append(entry)
        else:
            crew.append(entry)
    return {"cast": cast[:15], "crew": crew}


async def get_tv_credits(client: KinopoiskClient, film_id: int) -> dict:
    return await get_movie_credits(client, film_id)


async def get_movie_reviews(client: KinopoiskClient, film_id: int, page: int = 1) -> dict:
    """GET /api/v1/reviews?filmId={id}&page={page}&order=DATE_DESC"""
    try:
        data = await client.get("/api/v1/reviews", filmId=film_id, page=page, order="DATE_DESC")
        reviews = []
        for r in data.get("items", []):
            reviews.append({
                "author": r.get("author", "Аноним"),
                "author_details": {"rating": None},
                "content": r.get("description", ""),
                "created_at": r.get("date", ""),
                "type": r.get("type", ""),
            })
        return {
            "results": reviews,
            "total_pages": data.get("totalPages", 1),
            "total_results": data.get("total", len(reviews)),
        }
    except Exception:
        return {"results": [], "total_pages": 1, "total_results": 0}


async def get_movie_similar(client: KinopoiskClient, film_id: int) -> dict:
    """GET /api/v2.2/films/{id}/similars"""
    try:
        data = await client.get(f"/api/v2.2/films/{film_id}/similars")
        results = []
        for item in data.get("items", []):
            results.append({
                "id": item.get("filmId", 0),
                "media_type": "movie",
                "title": item.get("nameRu") or item.get("nameEn") or "—",
                "original_title": item.get("nameOriginal") or item.get("nameEn") or "—",
                "overview": "",
                "release_date": "",
                "genre_ids": [],
                "vote_average": 0.0,
                "vote_count": 0,
                "popularity": 0.0,
            })
        return {"results": results, "total_results": len(results)}
    except Exception:
        return {"results": [], "total_results": 0}


async def get_tv_similar(client: KinopoiskClient, film_id: int) -> dict:
    return await get_movie_similar(client, film_id)


async def get_movie_recommendations(client: KinopoiskClient, film_id: int, page: int = 1) -> dict:
    return await get_movie_similar(client, film_id)


async def get_tv_recommendations(client: KinopoiskClient, film_id: int, page: int = 1) -> dict:
    return await get_movie_similar(client, film_id)


async def post_movie_rating(client: KinopoiskClient, film_id: int, rating: float, session_id: Optional[str] = None) -> bool:
    return False


async def post_tv_rating(client: KinopoiskClient, film_id: int, rating: float, session_id: Optional[str] = None) -> bool:
    return False


async def auto_detect_type(client: KinopoiskClient, film_id: int) -> Optional[str]:
    """Определяет тип контента (movie/tv) по ID."""
    try:
        data = await client.get(f"/api/v2.2/films/{film_id}")
        kp_type = data.get("type", "FILM")
        return "tv" if kp_type in {"TV_SERIES", "TV_SHOW", "MINI_SERIES"} else "movie"
    except Exception:
        return None
