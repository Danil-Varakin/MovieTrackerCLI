from __future__ import annotations

from movie_tracker.exceptions import InvalidRatingError, MovieTrackerError
from movie_tracker.utils.helpers import CONTENT_TYPES, STATUS_VALUES


def validate_content_type(value: str, *, allow_all: bool = True) -> str:
    normalized = value.lower()
    allowed = CONTENT_TYPES if allow_all else {"movie", "tv"}
    if normalized not in allowed:
        values = " | ".join(sorted(allowed))
        raise MovieTrackerError(f"Неверный тип контента: {value}. Допустимо: {values}")
    return normalized


def validate_status(value: str) -> str:
    normalized = value.lower()
    if normalized not in STATUS_VALUES:
        raise MovieTrackerError("Неверный статус. Допустимо: watched | unwatched | watching")
    return normalized


def validate_priority(value: int) -> int:
    if not 1 <= value <= 5:
        raise MovieTrackerError("Приоритет должен быть от 1 до 5")
    return value


def validate_rating(value: float) -> float:
    doubled = value * 2
    if value < 0.5 or value > 10.0 or doubled != int(doubled):
        raise InvalidRatingError("Оценка должна быть от 0.5 до 10.0 (кратно 0.5)")
    return value


def validate_page(value: int) -> int:
    if value < 1:
        raise MovieTrackerError("Номер страницы должен быть больше 0")
    return value


def validate_limit(value: int, *, minimum: int = 1, maximum: int = 100) -> int:
    if not minimum <= value <= maximum:
        raise MovieTrackerError(f"Лимит должен быть от {minimum} до {maximum}")
    return value
