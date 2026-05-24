from __future__ import annotations

import pytest

from movie_tracker.exceptions import InvalidRatingError, MovieTrackerError
from movie_tracker.utils.validators import (
    validate_content_type,
    validate_priority,
    validate_rating,
    validate_status,
)


def test_validate_rating_accepts_half_step() -> None:
    assert validate_rating(9.5) == 9.5


def test_validate_rating_rejects_invalid_step() -> None:
    with pytest.raises(InvalidRatingError):
        validate_rating(9.3)


def test_validate_status_and_type() -> None:
    assert validate_status("watched") == "watched"
    assert validate_content_type("tv") == "tv"


def test_validate_priority_rejects_out_of_range() -> None:
    with pytest.raises(MovieTrackerError):
        validate_priority(6)
