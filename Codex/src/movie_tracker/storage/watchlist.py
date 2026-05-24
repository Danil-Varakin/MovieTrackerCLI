from __future__ import annotations

from collections import Counter
from typing import Any, cast

from tinydb import Query, TinyDB
from tinydb.storages import JSONStorage

from movie_tracker.config import AppConfig
from movie_tracker.exceptions import DuplicateWatchlistError, NotFoundError, WatchlistCorruptedError
from movie_tracker.models.movie import MediaItem
from movie_tracker.utils.helpers import now_iso


class WatchlistStore:
    def __init__(self, config: AppConfig) -> None:
        self.path = config.watchlist_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.db = TinyDB(self.path, storage=JSONStorage, ensure_ascii=False, indent=2)
        except Exception as exc:  # pragma: no cover - TinyDB wraps several JSON errors
            raise WatchlistCorruptedError(f"Файл watchlist повреждён: {self.path}") from exc
        self.table = self.db.table("items")

    def add(
        self,
        item: MediaItem,
        *,
        status: str = "unwatched",
        priority: int = 3,
        note: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if self.get(item.id):
            raise DuplicateWatchlistError(
                f"Kinopoisk ID {item.id} уже есть в watchlist. Используйте watchlist update."
            )
        timestamp = now_iso()
        record = {
            **item.to_dict(),
            "status": status,
            "priority": priority,
            "note": note,
            "tags": tags or [],
            "user_rating": None,
            "review": "",
            "added_at": timestamp,
            "updated_at": timestamp,
        }
        self.table.insert(record)
        return record

    def get(self, item_id: int) -> dict[str, Any] | None:
        Item = Query()
        return cast(dict[str, Any] | None, self.table.get(Item.id == int(item_id)))

    def list(
        self,
        *,
        status: str = "all",
        content_type: str = "all",
        tags: list[str] | None = None,
        search: str | None = None,
        sort: str = "added",
        order: str = "desc",
    ) -> list[dict[str, Any]]:
        rows = cast(list[dict[str, Any]], list(self.table.all()))
        if status != "all":
            rows = [row for row in rows if row.get("status") == status]
        if content_type != "all":
            rows = [row for row in rows if row.get("media_type") == content_type]
        if tags:
            wanted = {tag.lower() for tag in tags}
            rows = [
                row
                for row in rows
                if wanted.issubset({str(tag).lower() for tag in row.get("tags", [])})
            ]
        if search:
            needle = search.lower()
            rows = [row for row in rows if needle in str(row.get("title", "")).lower()]

        def rating_value(row: dict[str, Any]) -> float:
            raw = row.get("user_rating") or row.get("rating") or 0
            try:
                return float(raw)
            except (TypeError, ValueError):
                return 0.0

        key_map = {
            "added": lambda row: row.get("added_at", ""),
            "priority": lambda row: row.get("priority") or 0,
            "rating": rating_value,
            "title": lambda row: str(row.get("title", "")).lower(),
            "year": lambda row: row.get("year") or "",
        }
        reverse = order == "desc"
        rows.sort(key=key_map.get(sort, key_map["added"]), reverse=reverse)
        return rows

    def update(self, item_id: int, **changes: Any) -> dict[str, Any]:
        existing = self.get(item_id)
        if not existing:
            raise NotFoundError(f"Запись с Kinopoisk ID {item_id} не найдена в watchlist.")
        changes = {key: value for key, value in changes.items() if value is not None}
        if not changes:
            return existing
        changes["updated_at"] = now_iso()
        Item = Query()
        self.table.update(changes, Item.id == int(item_id))
        return self.get(item_id) or existing

    def rate(self, item_id: int, rating: float, *, review: str | None = None) -> dict[str, Any]:
        changes: dict[str, Any] = {"user_rating": rating, "status": "watched"}
        if review is not None:
            changes["review"] = review
        return self.update(item_id, **changes)

    def remove(self, item_id: int) -> bool:
        Item = Query()
        removed = self.table.remove(Item.id == int(item_id))
        return bool(removed)

    def stats(self) -> dict[str, Any]:
        rows = list(self.table.all())
        total = len(rows)
        statuses = Counter(row.get("status", "unwatched") for row in rows)
        ratings = [float(row["user_rating"]) for row in rows if row.get("user_rating") is not None]
        genres = Counter(genre for row in rows for genre in row.get("genres", []))
        watched = statuses.get("watched", 0)
        return {
            "total": total,
            "watched": watched,
            "unwatched": statuses.get("unwatched", 0),
            "watching": statuses.get("watching", 0),
            "watched_percent": round((watched / total) * 100, 1) if total else 0,
            "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else None,
            "top_genres": genres.most_common(5),
        }
