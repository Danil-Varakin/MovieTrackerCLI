from __future__ import annotations

from movie_tracker.config import load_config
from movie_tracker.models.movie import MediaItem
from movie_tracker.storage.watchlist import WatchlistStore


def test_watchlist_add_list_rate_and_stats() -> None:
    config = load_config()
    store = WatchlistStore(config)
    item = MediaItem(
        id=301,
        title="Матрица",
        media_type="movie",
        year="1999",
        rating="8.5",
        genres=["фантастика", "боевик"],
    )

    record = store.add(item, priority=5, tags=["classic"])
    assert record["title"] == "Матрица"

    rows = store.list(sort="priority")
    assert len(rows) == 1
    assert rows[0]["priority"] == 5

    rated = store.rate(301, 9.5, review="Отлично")
    assert rated["status"] == "watched"
    assert rated["user_rating"] == 9.5

    stats = store.stats()
    assert stats["total"] == 1
    assert stats["watched"] == 1
    assert stats["average_rating"] == 9.5
