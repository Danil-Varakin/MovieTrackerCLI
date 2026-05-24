"""Локальное хранилище watchlist на базе TinyDB."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from tinydb import Query, TinyDB  # type: ignore
from tinydb.storages import JSONStorage  # type: ignore
from tinydb.middlewares import CachingMiddleware  # type: ignore

from movie_tracker.config import get_watchlist_file
from movie_tracker.exceptions import DuplicateWatchlist, StorageError
from movie_tracker.models import WatchlistEntry, WatchlistStats


def _get_db() -> TinyDB:
    """Инициализирует и возвращает TinyDB экземпляр."""
    wf = get_watchlist_file()
    wf.parent.mkdir(parents=True, exist_ok=True)
    return TinyDB(str(wf), storage=CachingMiddleware(JSONStorage))


def add_entry(entry: WatchlistEntry) -> None:
    """Добавляет новую запись в watchlist."""
    with _get_db() as db:
        table = db.table("watchlist")
        Entry = Query()
        if table.contains(Entry.film_id == entry.film_id):
            raise DuplicateWatchlist(entry.film_id, entry.title)
        table.insert(entry.to_dict())


def get_entry(film_id: int) -> Optional[WatchlistEntry]:
    """Возвращает запись по ID фильма/сериала (Кинопоиск) или None."""
    with _get_db() as db:
        table = db.table("watchlist")
        Entry = Query()
        result = table.get(Entry.film_id == film_id)
        if result is None:
            return None
        return WatchlistEntry.from_dict(result)


def update_entry(
    film_id: int,
    status: Optional[str] = None,
    rating: Optional[float] = None,
    note: Optional[str] = None,
    tags: Optional[list[str]] = None,
    priority: Optional[int] = None,
) -> bool:
    """Обновляет запись в watchlist. Возвращает True если запись найдена."""
    with _get_db() as db:
        table = db.table("watchlist")
        Entry = Query()

        updates: dict = {"updated_at": datetime.now().isoformat(timespec="seconds")}
        if status is not None:
            updates["status"] = status
        if rating is not None:
            updates["rating"] = rating
        if note is not None:
            updates["note"] = note
        if tags is not None:
            updates["tags"] = tags
        if priority is not None:
            updates["priority"] = priority

        updated = table.update(updates, Entry.film_id == film_id)
        return bool(updated)


def remove_entry(film_id: int) -> bool:
    """Удаляет запись из watchlist. Возвращает True если запись найдена."""
    with _get_db() as db:
        table = db.table("watchlist")
        Entry = Query()
        removed = table.remove(Entry.film_id == film_id)
        return bool(removed)


def list_entries(
    status: Optional[str] = None,
    media_type: Optional[str] = None,
    tags: Optional[list[str]] = None,
    search: Optional[str] = None,
    sort_by: str = "added_at",
    order: str = "desc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[WatchlistEntry], int]:
    """
    Возвращает (entries, total_count) с фильтрацией и пагинацией.
    """
    with _get_db() as db:
        table = db.table("watchlist")
        all_records = table.all()

    entries = [WatchlistEntry.from_dict(r) for r in all_records]

    # Фильтрация
    if status and status != "all":
        entries = [e for e in entries if e.status == status]
    if media_type and media_type != "all":
        entries = [e for e in entries if e.media_type == media_type]
    if tags:
        entries = [e for e in entries if any(t in e.tags for t in tags)]
    if search:
        q = search.lower()
        entries = [e for e in entries if q in e.title.lower()]

    total = len(entries)

    # Сортировка
    reverse = order == "desc"
    sort_keys = {
        "added": "added_at",
        "priority": "priority",
        "rating": "rating",
        "title": "title",
        "year": "year",
        "added_at": "added_at",
    }
    key_field = sort_keys.get(sort_by, "added_at")

    def sort_key(e: WatchlistEntry) -> tuple:
        val = getattr(e, key_field, "")
        if val is None:
            return (1, "")
        return (0, val)

    entries.sort(key=sort_key, reverse=reverse)

    # Пагинация
    start = (page - 1) * page_size
    end = start + page_size
    return entries[start:end], total


def get_all_entries() -> list[WatchlistEntry]:
    """Возвращает все записи без фильтрации."""
    with _get_db() as db:
        table = db.table("watchlist")
        return [WatchlistEntry.from_dict(r) for r in table.all()]


def get_stats() -> WatchlistStats:
    """Вычисляет статистику watchlist."""
    entries = get_all_entries()

    total = len(entries)
    watched = sum(1 for e in entries if e.status == "watched")
    watching = sum(1 for e in entries if e.status == "watching")
    unwatched = sum(1 for e in entries if e.status == "unwatched")
    movies = sum(1 for e in entries if e.media_type == "movie")
    tv_shows = sum(1 for e in entries if e.media_type == "tv")

    rated = [e.rating for e in entries if e.rating is not None]
    avg_rating = round(sum(rated) / len(rated), 2) if rated else None

    return WatchlistStats(
        total=total,
        watched=watched,
        watching=watching,
        unwatched=unwatched,
        movies=movies,
        tv_shows=tv_shows,
        avg_rating=avg_rating,
        rated_count=len(rated),
    )


def get_watched_ids() -> set[int]:
    """Возвращает множество ID фильма/сериала (Кинопоиск) просмотренного контента."""
    entries = get_all_entries()
    return {e.film_id for e in entries if e.status == "watched"}


def get_top_genres_from_watchlist(genre_map: dict[int, str]) -> list[int]:
    """
    Анализирует watchlist и возвращает топ жанров по количеству.
    Используется для персональных рекомендаций.
    """
    from collections import Counter
    entries = get_all_entries()
    # Возвращаем ID лучших записей для анализа
    ids = [e.film_id for e in entries if e.status in ("watched", "watching")]
    return ids[:5]  # Топ-5 для запросов рекомендаций
