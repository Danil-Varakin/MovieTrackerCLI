"""Unit тесты валидаторов."""

from __future__ import annotations

import pytest
from movie_tracker.exceptions import InvalidRating
from movie_tracker.utils.validators import (
    format_runtime,
    map_sort_field,
    mask_api_key,
    parse_tags,
    resolve_genre_id,
    validate_limit,
    validate_page,
    validate_priority,
    validate_rating,
    validate_year,
)


class TestValidateRating:
    def test_valid_ratings(self):
        assert validate_rating(0.5) == 0.5
        assert validate_rating(10.0) == 10.0
        assert validate_rating(7.5) == 7.5
        assert validate_rating(8.0) == 8.0

    def test_rounds_to_nearest_half(self):
        assert validate_rating(7.3) == 7.5
        assert validate_rating(7.1) == 7.0

    def test_invalid_below_range(self):
        with pytest.raises(InvalidRating):
            validate_rating(0.0)

    def test_invalid_above_range(self):
        with pytest.raises(InvalidRating):
            validate_rating(10.5)

    def test_invalid_negative(self):
        with pytest.raises(InvalidRating):
            validate_rating(-1.0)


class TestParseTags:
    def test_simple_tags(self):
        assert parse_tags("drama,cult,favorite") == ["drama", "cult", "favorite"]

    def test_strips_whitespace(self):
        assert parse_tags("drama, cult , favorite") == ["drama", "cult", "favorite"]

    def test_empty_string(self):
        assert parse_tags("") == []

    def test_none(self):
        assert parse_tags(None) == []

    def test_single_tag(self):
        assert parse_tags("drama") == ["drama"]

    def test_filters_empty_segments(self):
        assert parse_tags("drama,,cult") == ["drama", "cult"]


class TestValidateYear:
    def test_valid_year(self):
        assert validate_year("2024") == "2024"
        assert validate_year("1999") == "1999"

    def test_invalid_format(self):
        assert validate_year("99") is None
        assert validate_year("20240") is None
        assert validate_year("abcd") is None

    def test_none_returns_none(self):
        assert validate_year(None) is None


class TestValidatePage:
    def test_valid_page(self):
        assert validate_page(1) == 1
        assert validate_page(5) == 5

    def test_zero_becomes_one(self):
        assert validate_page(0) == 1

    def test_negative_becomes_one(self):
        assert validate_page(-5) == 1


class TestValidatePriority:
    def test_valid_priority(self):
        assert validate_priority(1) == 1
        assert validate_priority(5) == 5
        assert validate_priority(3) == 3

    def test_below_range(self):
        assert validate_priority(0) == 1

    def test_above_range(self):
        assert validate_priority(6) == 5


class TestValidateLimit:
    def test_valid_limit(self):
        assert validate_limit(10, 100) == 10

    def test_exceeds_max(self):
        assert validate_limit(150, 100) == 100

    def test_zero_becomes_one(self):
        assert validate_limit(0, 100) == 1


class TestMapSortField:
    def test_popularity(self):
        assert map_sort_field("popularity") == "popularity.desc"

    def test_rating(self):
        assert map_sort_field("rating") == "vote_average.desc"

    def test_year(self):
        assert map_sort_field("year") == "primary_release_date.desc"

    def test_unknown_defaults_to_popularity(self):
        assert map_sort_field("unknown_field") == "popularity.desc"

    def test_none_defaults_to_popularity(self):
        assert map_sort_field(None) == "popularity.desc"


class TestMaskApiKey:
    def test_long_key(self):
        key = "abcd1234efgh5678"
        masked = mask_api_key(key)
        assert masked.startswith("abcd")
        assert masked.endswith("5678")
        assert "***" in masked

    def test_short_key(self):
        assert mask_api_key("abc") == "***"

    def test_empty_key(self):
        assert mask_api_key("") == "***"


class TestFormatRuntime:
    def test_hours_and_minutes(self):
        assert format_runtime(139) == "2ч 19мин"

    def test_only_minutes(self):
        assert format_runtime(45) == "45мин"

    def test_none(self):
        assert format_runtime(None) == "—"

    def test_zero(self):
        assert format_runtime(0) == "—"


class TestResolveGenreId:
    GENRE_MAP = {
        28: "Action",
        18: "Drama",
        53: "Thriller",
        35: "Comedy",
    }

    def test_by_numeric_id(self):
        result = resolve_genre_id("28", self.GENRE_MAP)
        assert result == "28"

    def test_by_name_exact(self):
        result = resolve_genre_id("Action", self.GENRE_MAP)
        assert result == "28"

    def test_by_name_case_insensitive(self):
        result = resolve_genre_id("drama", self.GENRE_MAP)
        assert result == "18"

    def test_unknown_name_returns_none(self):
        result = resolve_genre_id("SciFi", self.GENRE_MAP)
        assert result is None
