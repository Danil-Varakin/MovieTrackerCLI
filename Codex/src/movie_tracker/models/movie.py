from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from movie_tracker.utils.helpers import (
    normalize_countries,
    normalize_genres,
    normalize_type,
    pick_title,
    truncate,
)


@dataclass
class MediaItem:
    id: int
    title: str
    media_type: str
    year: str = ""
    rating: str = ""
    rating_imdb: str = ""
    votes: int | None = None
    genres: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    description: str = ""
    poster_url: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> MediaItem:
        item_id = payload.get("kinopoiskId") or payload.get("filmId") or payload.get("id")
        if item_id is None:
            raise ValueError("Kinopoisk payload does not contain an ID")
        rating = (
            payload.get("ratingKinopoisk") or payload.get("rating") or payload.get("ratingImdb")
        )
        if rating in {None, "null"}:
            rating = ""
        votes = payload.get("ratingKinopoiskVoteCount") or payload.get("ratingVoteCount")
        year = payload.get("year") or payload.get("startYear") or ""
        return cls(
            id=int(item_id),
            title=pick_title(payload),
            media_type=normalize_type(payload.get("type")),
            year=str(year or ""),
            rating=str(rating or ""),
            rating_imdb=str(payload.get("ratingImdb") or ""),
            votes=int(votes) if isinstance(votes, int | float) else None,
            genres=normalize_genres(payload.get("genres")),
            countries=normalize_countries(payload.get("countries")),
            description=truncate(
                payload.get("description") or payload.get("shortDescription"), 280
            ),
            poster_url=str(payload.get("posterUrlPreview") or payload.get("posterUrl") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
