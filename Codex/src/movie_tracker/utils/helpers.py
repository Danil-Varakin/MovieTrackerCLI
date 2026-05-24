from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

CONTENT_TYPES = {"movie", "tv", "all"}
STATUS_VALUES = {"unwatched", "watched", "watching"}

GENRE_ALIASES = {
    "action": "боевик",
    "adventure": "приключения",
    "animation": "мультфильм",
    "comedy": "комедия",
    "crime": "криминал",
    "documentary": "документальный",
    "drama": "драма",
    "family": "семейный",
    "fantasy": "фэнтези",
    "history": "история",
    "horror": "ужасы",
    "music": "музыка",
    "mystery": "детектив",
    "romance": "мелодрама",
    "sci-fi": "фантастика",
    "science fiction": "фантастика",
    "thriller": "триллер",
    "war": "военный",
    "western": "вестерн",
}


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def parse_tags(value: str | None) -> list[str]:
    if not value:
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def truncate(value: str | None, max_length: int = 100) -> str:
    text = (value or "").strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"


def normalize_type(api_type: str | None) -> str:
    value = (api_type or "").upper()
    if value in {"TV_SERIES", "MINI_SERIES", "TV_SHOW"}:
        return "tv"
    return "movie"


def to_kinopoisk_type(content_type: str) -> str:
    if content_type == "movie":
        return "FILM"
    if content_type == "tv":
        return "TV_SERIES"
    return "ALL"


def display_type(content_type: str | None) -> str:
    return {"movie": "Фильм", "tv": "Сериал", "all": "Все"}.get(
        content_type or "", content_type or "-"
    )


def normalize_genres(genres: list[dict[str, Any]] | list[str] | None) -> list[str]:
    if not genres:
        return []
    normalized: list[str] = []
    for genre in genres:
        value = genre.get("genre") or genre.get("name") if isinstance(genre, dict) else genre
        if value:
            normalized.append(str(value))
    return normalized


def normalize_countries(countries: list[dict[str, Any]] | None) -> list[str]:
    if not countries:
        return []
    values: list[str] = []
    for country in countries:
        value = country.get("country") or country.get("name")
        if value:
            values.append(str(value))
    return values


def pick_title(payload: dict[str, Any]) -> str:
    return (
        payload.get("nameRu")
        or payload.get("nameOriginal")
        or payload.get("nameEn")
        or payload.get("name")
        or payload.get("title")
        or f"Kinopoisk ID {payload.get('kinopoiskId') or payload.get('filmId') or payload.get('id')}"
    )


def masked_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}***{value[-4:]}"


def genre_lookup_key(value: str) -> str:
    normalized = value.strip().lower()
    return GENRE_ALIASES.get(normalized, normalized)
