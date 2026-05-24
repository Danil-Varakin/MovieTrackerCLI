from __future__ import annotations

from movie_tracker.exceptions import UnsupportedFeatureError


def raise_remote_watchlist_unsupported() -> None:
    raise UnsupportedFeatureError(
        "Kinopoisk API Unofficial не поддерживает удалённую синхронизацию watchlist. "
        "MovieTracker CLI Codex хранит watchlist локально."
    )
