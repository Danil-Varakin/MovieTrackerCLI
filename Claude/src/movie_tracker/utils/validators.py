"""Вспомогательные утилиты и валидаторы."""

from __future__ import annotations

import re
from typing import Optional

from movie_tracker.exceptions import InvalidRating


def validate_rating(rating: float) -> float:
    """Валидирует и возвращает рейтинг. Бросает InvalidRating если недопустим."""
    # Округляем до ближайшего 0.5
    rounded = round(rating * 2) / 2
    if rounded < 0.5 or rounded > 10.0:
        raise InvalidRating()
    return rounded


def parse_tags(tags_str: Optional[str]) -> list[str]:
    """Парсит строку тегов вида 'drama,cult,favorite' в список."""
    if not tags_str:
        return []
    return [t.strip() for t in tags_str.split(",") if t.strip()]


def parse_genre_filter(genre: Optional[str]) -> Optional[str]:
    """
    Принимает ID или название жанра.
    Если строка — числовая, возвращает как есть.
    Иначе возвращает строку для поиска по имени.
    """
    if not genre:
        return None
    return genre.strip()


def is_genre_id(genre: str) -> bool:
    """Возвращает True если жанр передан как числовой ID."""
    return genre.isdigit()


def resolve_genre_id(genre: str, genre_map: dict[int, str]) -> Optional[str]:
    """
    Возвращает ID жанра (строка) по имени или числовому ID.
    Поиск по имени — case-insensitive.
    """
    if is_genre_id(genre):
        return genre

    genre_lower = genre.lower()
    for gid, gname in genre_map.items():
        if gname.lower() == genre_lower:
            return str(gid)
    return None


SORT_MAP = {
    "relevance": "popularity.desc",  # Кинопоиск не имеет "relevance" в discover
    "popularity": "popularity.desc",
    "rating": "vote_average.desc",
    "year": "primary_release_date.desc",
    "year_asc": "primary_release_date.asc",
}


def map_sort_field(sort: Optional[str], media_type: str = "movie") -> str:
    """Преобразует пользовательское поле сортировки в Кинопоиске sort_by."""
    if not sort:
        return "popularity.desc"
    if sort in SORT_MAP:
        return SORT_MAP[sort]
    return "popularity.desc"


def detect_media_type_from_api(film_id: int) -> Optional[str]:
    """
    Пытается определить тип контента (movie/tv) по ID.
    Используется когда --type не указан.
    Заглушка — реальное определение делается через API.
    """
    return None


def mask_api_key(key: str) -> str:
    """Маскирует API ключ для логов: sk-***...xxx."""
    if not key or len(key) <= 8:
        return "***"
    return key[:4] + "***" + key[-4:]


def format_runtime(minutes: Optional[int]) -> str:
    if not minutes:
        return "—"
    h, m = divmod(minutes, 60)
    if h:
        return f"{h}ч {m}мин"
    return f"{m}мин"


def truncate_text(text: str, max_len: int = 200) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def validate_year(year: Optional[str]) -> Optional[str]:
    """Валидирует год (4 цифры)."""
    if not year:
        return None
    if re.match(r"^\d{4}$", year):
        return year
    return None


def validate_page(page: int) -> int:
    """Гарантирует что страница >= 1."""
    return max(1, page)


def validate_priority(priority: int) -> int:
    """Гарантирует приоритет в диапазоне 1-5."""
    return max(1, min(5, priority))


def validate_limit(limit: int, max_limit: int = 100) -> int:
    """Ограничивает limit сверху."""
    return max(1, min(limit, max_limit))
