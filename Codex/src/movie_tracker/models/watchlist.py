from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WatchlistEntry:
    id: int
    title: str
    media_type: str
    status: str = "unwatched"
    priority: int = 3
    tags: list[str] = field(default_factory=list)
    note: str = ""
    user_rating: float | None = None
    review: str = ""
