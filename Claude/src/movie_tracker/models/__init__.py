"""Модели данных MovieTracker CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────────────────────
# Базовые модели Кинопоиск
# ─────────────────────────────────────────────────────────────


@dataclass
class Genre:
    id: int
    name: str


@dataclass
class ProductionCompany:
    id: int
    name: str
    origin_country: str = ""


@dataclass
class SearchResult:
    """Результат поиска (фильм или сериал)."""

    id: int
    media_type: str  # "movie" | "tv"
    title: str
    original_title: str
    overview: str
    year: str
    genre_ids: list[int] = field(default_factory=list)
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0
    poster_path: Optional[str] = None
    genre_names_str: str = ""  # текстовые жанры Кинопоиска

    @classmethod
    def from_api(cls, data: dict) -> "SearchResult":
        media_type = data.get("media_type", "movie")
        if media_type == "tv":
            title = data.get("name", data.get("original_name", data.get("title", "N/A")))
            original_title = data.get("original_name", data.get("original_title", title))
            date_field = data.get("first_air_date", data.get("release_date", ""))
        else:
            title = data.get("title", data.get("original_title", "N/A"))
            original_title = data.get("original_title", title)
            date_field = data.get("release_date", "")

        year = date_field[:4] if date_field else "—"

        return cls(
            id=data["id"],
            media_type=media_type,
            title=title,
            original_title=original_title,
            overview=data.get("overview", ""),
            year=year,
            genre_ids=data.get("genre_ids", []),
            vote_average=data.get("vote_average", 0.0),
            vote_count=data.get("vote_count", 0),
            popularity=data.get("popularity", 0.0),
            poster_path=data.get("poster_path"),
            genre_names_str=", ".join(data.get("genre_names", [])[:3]),
        )


@dataclass
class MovieDetails:
    """Детальная информация о фильме."""

    id: int
    title: str
    original_title: str
    overview: str
    release_date: str
    runtime: Optional[int]
    genres: list[Genre]
    vote_average: float
    vote_count: int
    popularity: float
    budget: int
    revenue: int
    status: str
    tagline: str
    imdb_id: Optional[str]
    production_countries: list[str]
    spoken_languages: list[str]
    poster_path: Optional[str]
    backdrop_path: Optional[str]

    @property
    def year(self) -> str:
        return self.release_date[:4] if self.release_date else "—"

    @classmethod
    def from_api(cls, data: dict) -> "MovieDetails":
        genres = [Genre(g["id"], g["name"]) for g in data.get("genres", [])]
        countries = [c.get("name", "") for c in data.get("production_countries", [])]
        languages = [
            lang.get("english_name", lang.get("name", ""))
            for lang in data.get("spoken_languages", [])
        ]
        return cls(
            id=data["id"],
            title=data.get("title", "N/A"),
            original_title=data.get("original_title", ""),
            overview=data.get("overview", ""),
            release_date=data.get("release_date", ""),
            runtime=data.get("runtime"),
            genres=genres,
            vote_average=data.get("vote_average", 0.0),
            vote_count=data.get("vote_count", 0),
            popularity=data.get("popularity", 0.0),
            budget=data.get("budget", 0),
            revenue=data.get("revenue", 0),
            status=data.get("status", ""),
            tagline=data.get("tagline", ""),
            imdb_id=data.get("imdb_id"),
            production_countries=countries,
            spoken_languages=languages,
            poster_path=data.get("poster_path"),
            backdrop_path=data.get("backdrop_path"),
        )


@dataclass
class TVDetails:
    """Детальная информация о сериале."""

    id: int
    name: str
    original_name: str
    overview: str
    first_air_date: str
    last_air_date: str
    number_of_seasons: int
    number_of_episodes: int
    status: str
    type: str
    genres: list[Genre]
    vote_average: float
    vote_count: int
    popularity: float
    networks: list[str]
    origin_country: list[str]
    in_production: bool
    tagline: str
    poster_path: Optional[str]
    backdrop_path: Optional[str]

    @property
    def year(self) -> str:
        return self.first_air_date[:4] if self.first_air_date else "—"

    @classmethod
    def from_api(cls, data: dict) -> "TVDetails":
        genres = [Genre(g["id"], g["name"]) for g in data.get("genres", [])]
        networks = [n.get("name", "") for n in data.get("networks", [])]
        return cls(
            id=data["id"],
            name=data.get("name", "N/A"),
            original_name=data.get("original_name", ""),
            overview=data.get("overview", ""),
            first_air_date=data.get("first_air_date", ""),
            last_air_date=data.get("last_air_date", ""),
            number_of_seasons=data.get("number_of_seasons", 0),
            number_of_episodes=data.get("number_of_episodes", 0),
            status=data.get("status", ""),
            type=data.get("type", ""),
            genres=genres,
            vote_average=data.get("vote_average", 0.0),
            vote_count=data.get("vote_count", 0),
            popularity=data.get("popularity", 0.0),
            networks=networks,
            origin_country=data.get("origin_country", []),
            in_production=data.get("in_production", False),
            tagline=data.get("tagline", ""),
            poster_path=data.get("poster_path"),
            backdrop_path=data.get("backdrop_path"),
        )


@dataclass
class CastMember:
    id: int
    name: str
    character: str
    order: int
    profile_path: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict) -> "CastMember":
        return cls(
            id=data["id"],
            name=data.get("name", "N/A"),
            character=data.get("character", ""),
            order=data.get("order", 0),
            profile_path=data.get("profile_path"),
        )


@dataclass
class CrewMember:
    id: int
    name: str
    job: str
    department: str
    profile_path: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict) -> "CrewMember":
        return cls(
            id=data["id"],
            name=data.get("name", "N/A"),
            job=data.get("job", ""),
            department=data.get("department", ""),
            profile_path=data.get("profile_path"),
        )


@dataclass
class Credits:
    cast: list[CastMember]
    crew: list[CrewMember]

    @property
    def directors(self) -> list[CrewMember]:
        return [c for c in self.crew if c.job == "Director"]

    @property
    def writers(self) -> list[CrewMember]:
        return [c for c in self.crew if c.department == "Writing"]

    @classmethod
    def from_api(cls, data: dict) -> "Credits":
        cast = [CastMember.from_api(m) for m in data.get("cast", [])]
        crew = [CrewMember.from_api(m) for m in data.get("crew", [])]
        return cls(cast=sorted(cast, key=lambda x: x.order), crew=crew)


@dataclass
class Review:
    id: str
    author: str
    rating: Optional[float]
    content: str
    created_at: str
    url: str

    @classmethod
    def from_api(cls, data: dict) -> "Review":
        rating = None
        author_details = data.get("author_details", {})
        if author_details.get("rating"):
            rating = float(author_details["rating"])
        return cls(
            id=data.get("id", ""),
            author=data.get("author", "Аноним"),
            rating=rating,
            content=data.get("content", ""),
            created_at=data.get("created_at", "")[:10],
            url=data.get("url", ""),
        )


@dataclass
class SearchPage:
    """Страница результатов поиска."""

    page: int
    total_pages: int
    total_results: int
    results: list[SearchResult]

    @classmethod
    def from_api(cls, data: dict) -> "SearchPage":
        results = [SearchResult.from_api(r) for r in data.get("results", [])]
        return cls(
            page=data.get("page", 1),
            total_pages=data.get("total_pages", 1),
            total_results=data.get("total_results", len(results)),
            results=results,
        )


# ─────────────────────────────────────────────────────────────
# Модели Watchlist
# ─────────────────────────────────────────────────────────────


@dataclass
class WatchlistEntry:
    """Запись в watchlist."""

    film_id: int
    media_type: str  # "movie" | "tv"
    title: str
    year: str
    status: str  # "unwatched" | "watching" | "watched"
    priority: int  # 1-5
    rating: Optional[float]
    note: str
    tags: list[str]
    added_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return {
            "film_id": self.film_id,
            "media_type": self.media_type,
            "title": self.title,
            "year": self.year,
            "status": self.status,
            "priority": self.priority,
            "rating": self.rating,
            "note": self.note,
            "tags": self.tags,
            "added_at": self.added_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WatchlistEntry":
        return cls(
            film_id=data["film_id"],
            media_type=data.get("media_type", "movie"),
            title=data.get("title", "N/A"),
            year=data.get("year", "—"),
            status=data.get("status", "unwatched"),
            priority=data.get("priority", 3),
            rating=data.get("rating"),
            note=data.get("note", ""),
            tags=data.get("tags", []),
            added_at=data.get("added_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    @classmethod
    def new(
        cls,
        film_id: int,
        media_type: str,
        title: str,
        year: str,
        status: str = "unwatched",
        priority: int = 3,
        note: str = "",
        tags: Optional[list[str]] = None,
    ) -> "WatchlistEntry":
        now = datetime.now().isoformat(timespec="seconds")
        return cls(
            film_id=film_id,
            media_type=media_type,
            title=title,
            year=year,
            status=status,
            priority=priority,
            rating=None,
            note=note,
            tags=tags or [],
            added_at=now,
            updated_at=now,
        )


@dataclass
class WatchlistStats:
    total: int
    watched: int
    watching: int
    unwatched: int
    movies: int
    tv_shows: int
    avg_rating: Optional[float]
    rated_count: int

    @property
    def watched_percent(self) -> float:
        return round(self.watched / self.total * 100, 1) if self.total else 0.0


# ─────────────────────────────────────────────────────────────
# Модели аутентификации
# ─────────────────────────────────────────────────────────────


@dataclass
class AuthInfo:
    username: str
    account_id: int
    session_id: str
    logged_in_at: str

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "account_id": self.account_id,
            "session_id": self.session_id,
            "logged_in_at": self.logged_in_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuthInfo":
        return cls(
            username=data["username"],
            account_id=data["account_id"],
            session_id=data["session_id"],
            logged_in_at=data.get("logged_in_at", ""),
        )
