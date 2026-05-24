from __future__ import annotations

from movie_tracker.exceptions import UnsupportedFeatureError


def raise_oauth_unsupported() -> None:
    raise UnsupportedFeatureError(
        "Kinopoisk API Unofficial не предоставляет OAuth-login. "
        "Используйте: movie-tracker auth token YOUR_KINOPOISK_API_KEY"
    )
