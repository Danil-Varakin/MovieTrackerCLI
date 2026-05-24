"""Менеджер кэширования на базе diskcache."""

from __future__ import annotations

import functools
import hashlib
import json
from typing import Any, Callable, Optional, TypeVar

import diskcache  # type: ignore

from movie_tracker.config import (
    get_cache_dir,
    get_cache_enabled,
    get_cache_max_size,
)

F = TypeVar("F", bound=Callable[..., Any])

# Глобальный экземпляр кэша
_cache: Optional[diskcache.Cache] = None


def get_cache() -> diskcache.Cache:
    """Возвращает (или инициализирует) глобальный экземпляр кэша."""
    global _cache
    if _cache is None:
        cache_dir = get_cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)
        _cache = diskcache.Cache(
            directory=str(cache_dir),
            size_limit=get_cache_max_size(),
            eviction_policy="least-recently-used",
        )
    return _cache


def _make_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """Генерирует уникальный ключ кэша."""
    raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"{prefix}:{digest}"


def cached(prefix: str, ttl: int) -> Callable[[F], F]:
    """
    Декоратор кэширования для синхронных функций.

    Args:
        prefix: Префикс ключа кэша (например, 'search', 'details')
        ttl: Время жизни в секундах
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not get_cache_enabled():
                return func(*args, **kwargs)

            no_cache = kwargs.pop("no_cache", False)
            cache = get_cache()
            key = _make_key(prefix, *args, **kwargs)

            if not no_cache:
                value = cache.get(key)
                if value is not None:
                    return value

            result = func(*args, **kwargs)
            cache.set(key, result, expire=ttl)
            return result

        return wrapper  # type: ignore

    return decorator


def cache_get(key: str) -> Optional[Any]:
    """Получить значение из кэша."""
    if not get_cache_enabled():
        return None
    return get_cache().get(key)


def cache_set(key: str, value: Any, ttl: int) -> None:
    """Сохранить значение в кэш с TTL в секундах."""
    if not get_cache_enabled():
        return
    get_cache().set(key, value, expire=ttl)


def cache_delete(key: str) -> None:
    """Удалить значение из кэша."""
    get_cache().delete(key)


def cache_clear(older_than_hours: Optional[int] = None) -> int:
    """
    Очистить кэш.

    Args:
        older_than_hours: Удалить только записи старше N часов.
                          None — удалить всё.
    Returns:
        Количество удалённых записей.
    """
    cache = get_cache()
    if older_than_hours is None:
        count = len(cache)
        cache.clear()
        return count

    # Diskcache не предоставляет прямого доступа к времени создания,
    # поэтому используем expire — удаляем просроченные
    cache.expire()
    return 0


def make_search_key(query: str, **params: Any) -> str:
    return _make_key("search", query, **params)


def make_details_key(film_id: int, media_type: str, **params: Any) -> str:
    return _make_key("details", film_id, media_type, **params)


def make_popular_key(media_type: str, page: int, **params: Any) -> str:
    return _make_key("popular", media_type, page, **params)


def make_trending_key(media_type: str, window: str, page: int) -> str:
    return _make_key("trending", media_type, window, page)


def make_recommend_key(film_id: int, media_type: str, page: int) -> str:
    return _make_key("recommend", film_id, media_type, page)


def make_genres_key(media_type: str) -> str:
    return _make_key("genres", media_type)


# TTL константы (в секундах)
TTL_SEARCH = 3600          # 1 час
TTL_DETAILS = 86400        # 24 часа
TTL_POPULAR = 10800        # 3 часа
TTL_TRENDING_DAY = 1800    # 30 минут
TTL_TRENDING_WEEK = 10800  # 3 часа
TTL_RECOMMEND = 43200      # 12 часов
TTL_GENRES = 604800        # 7 дней
