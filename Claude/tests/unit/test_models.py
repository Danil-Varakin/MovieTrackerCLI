"""Unit тесты для моделей данных."""

from __future__ import annotations

import pytest
from movie_tracker.models import (
    AuthInfo,
    Credits,
    MovieDetails,
    SearchPage,
    SearchResult,
    TVDetails,
    WatchlistEntry,
    WatchlistStats,
)


class TestSearchResult:
    def test_from_api_movie(self):
        data = {
            "id": 550,
            "media_type": "movie",
            "title": "Fight Club",
            "original_title": "Fight Club",
            "overview": "Test overview",
            "release_date": "1999-10-15",
            "genre_ids": [18, 53],
            "vote_average": 8.4,
            "vote_count": 29150,
            "popularity": 76.3,
        }
        result = SearchResult.from_api(data)
        assert result.id == 550
        assert result.title == "Fight Club"
        assert result.media_type == "movie"
        assert result.year == "1999"
        assert result.vote_average == 8.4

    def test_from_api_tv(self):
        data = {
            "id": 1396,
            "media_type": "tv",
            "name": "Breaking Bad",
            "original_name": "Breaking Bad",
            "overview": "...",
            "first_air_date": "2008-01-20",
            "genre_ids": [18, 80],
            "vote_average": 9.5,
            "vote_count": 14000,
            "popularity": 230.0,
        }
        result = SearchResult.from_api(data)
        assert result.id == 1396
        assert result.title == "Breaking Bad"
        assert result.media_type == "tv"
        assert result.year == "2008"

    def test_missing_date_shows_dash(self):
        data = {
            "id": 999,
            "media_type": "movie",
            "title": "Unknown",
            "original_title": "Unknown",
            "overview": "",
            "release_date": "",
            "genre_ids": [],
            "vote_average": 0.0,
            "vote_count": 0,
            "popularity": 0.0,
        }
        result = SearchResult.from_api(data)
        assert result.year == "—"


class TestMovieDetails:
    def test_from_api(self, mock_movie_data):
        movie = MovieDetails.from_api(mock_movie_data)
        assert movie.id == 550
        assert movie.title == "Fight Club"
        assert movie.year == "1999"
        assert len(movie.genres) == 2
        assert movie.genres[0].name == "Drama"
        assert movie.imdb_id == "tt0137523"
        assert movie.budget == 63000000

    @pytest.fixture
    def mock_movie_data(self):
        return {
            "id": 550,
            "title": "Fight Club",
            "original_title": "Fight Club",
            "overview": "Test",
            "release_date": "1999-10-15",
            "runtime": 139,
            "genres": [{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}],
            "vote_average": 8.4,
            "vote_count": 29150,
            "popularity": 76.3,
            "budget": 63000000,
            "revenue": 101200000,
            "status": "Released",
            "tagline": "Mischief. Mayhem. Soap.",
            "imdb_id": "tt0137523",
            "production_countries": [{"name": "United States of America"}],
            "spoken_languages": [{"english_name": "English"}],
            "poster_path": None,
            "backdrop_path": None,
        }


class TestWatchlistEntry:
    def test_new_entry(self):
        entry = WatchlistEntry.new(
            film_id=550,
            media_type="movie",
            title="Fight Club",
            year="1999",
        )
        assert entry.film_id == 550
        assert entry.status == "unwatched"
        assert entry.priority == 3
        assert entry.rating is None
        assert entry.tags == []
        assert entry.added_at != ""

    def test_to_dict_and_back(self):
        entry = WatchlistEntry.new(
            film_id=1396,
            media_type="tv",
            title="Breaking Bad",
            year="2008",
            status="watching",
            priority=5,
            note="Great show",
            tags=["drama", "crime"],
        )
        d = entry.to_dict()
        restored = WatchlistEntry.from_dict(d)

        assert restored.film_id == 1396
        assert restored.title == "Breaking Bad"
        assert restored.status == "watching"
        assert restored.priority == 5
        assert restored.note == "Great show"
        assert restored.tags == ["drama", "crime"]

    def test_roundtrip_preserves_rating(self):
        entry = WatchlistEntry.new(550, "movie", "Fight Club", "1999")
        d = entry.to_dict()
        d["rating"] = 9.5
        restored = WatchlistEntry.from_dict(d)
        assert restored.rating == 9.5


class TestWatchlistStats:
    def test_watched_percent(self):
        stats = WatchlistStats(
            total=10,
            watched=7,
            watching=2,
            unwatched=1,
            movies=6,
            tv_shows=4,
            avg_rating=8.0,
            rated_count=5,
        )
        assert stats.watched_percent == 70.0

    def test_watched_percent_zero(self):
        stats = WatchlistStats(
            total=0,
            watched=0,
            watching=0,
            unwatched=0,
            movies=0,
            tv_shows=0,
            avg_rating=None,
            rated_count=0,
        )
        assert stats.watched_percent == 0.0


class TestSearchPage:
    def test_from_api(self):
        data = {
            "page": 1,
            "total_pages": 5,
            "total_results": 97,
            "results": [
                {
                    "id": 550,
                    "media_type": "movie",
                    "title": "Fight Club",
                    "original_title": "Fight Club",
                    "overview": "",
                    "release_date": "1999-10-15",
                    "genre_ids": [18],
                    "vote_average": 8.4,
                    "vote_count": 29150,
                    "popularity": 76.3,
                }
            ],
        }
        page = SearchPage.from_api(data)
        assert page.page == 1
        assert page.total_pages == 5
        assert page.total_results == 97
        assert len(page.results) == 1
        assert page.results[0].title == "Fight Club"
