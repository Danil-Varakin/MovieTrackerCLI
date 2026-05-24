"""Unit тесты для хранилища watchlist."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from movie_tracker.exceptions import DuplicateWatchlist
from movie_tracker.models import WatchlistEntry
from movie_tracker.storage import watchlist as wl


@pytest.fixture
def mock_wf(tmp_path: Path):
    """Подменяет watchlist файл на временный."""
    wf = tmp_path / "watchlist.json"
    with patch("movie_tracker.storage.watchlist.get_watchlist_file", return_value=wf):
        yield wf


@pytest.fixture
def entry_fight_club():
    return WatchlistEntry.new(550, "movie", "Fight Club", "1999")


@pytest.fixture
def entry_breaking_bad():
    return WatchlistEntry.new(1396, "tv", "Breaking Bad", "2008", status="watching", priority=5)


class TestAddEntry:
    def test_adds_entry_successfully(self, mock_wf, entry_fight_club):
        wl.add_entry(entry_fight_club)
        result = wl.get_entry(550)
        assert result is not None
        assert result.title == "Fight Club"

    def test_raises_on_duplicate(self, mock_wf, entry_fight_club):
        wl.add_entry(entry_fight_club)
        with pytest.raises(DuplicateWatchlist):
            wl.add_entry(entry_fight_club)

    def test_preserves_tags(self, mock_wf):
        entry = WatchlistEntry.new(550, "movie", "Fight Club", "1999", tags=["drama", "cult"])
        wl.add_entry(entry)
        result = wl.get_entry(550)
        assert result.tags == ["drama", "cult"]

    def test_preserves_note(self, mock_wf):
        entry = WatchlistEntry.new(550, "movie", "Fight Club", "1999", note="Watch with friends")
        wl.add_entry(entry)
        result = wl.get_entry(550)
        assert result.note == "Watch with friends"


class TestGetEntry:
    def test_returns_none_for_missing(self, mock_wf):
        result = wl.get_entry(9999)
        assert result is None

    def test_returns_correct_entry(self, mock_wf, entry_fight_club):
        wl.add_entry(entry_fight_club)
        result = wl.get_entry(550)
        assert result is not None
        assert result.film_id == 550
        assert result.media_type == "movie"


class TestUpdateEntry:
    def test_update_status(self, mock_wf, entry_fight_club):
        wl.add_entry(entry_fight_club)
        updated = wl.update_entry(550, status="watched")
        assert updated is True
        result = wl.get_entry(550)
        assert result.status == "watched"

    def test_update_rating(self, mock_wf, entry_fight_club):
        wl.add_entry(entry_fight_club)
        wl.update_entry(550, rating=9.5)
        result = wl.get_entry(550)
        assert result.rating == 9.5

    def test_update_tags(self, mock_wf, entry_fight_club):
        wl.add_entry(entry_fight_club)
        wl.update_entry(550, tags=["drama", "classic"])
        result = wl.get_entry(550)
        assert result.tags == ["drama", "classic"]

    def test_update_nonexistent_returns_false(self, mock_wf):
        updated = wl.update_entry(9999, status="watched")
        assert updated is False

    def test_updates_updated_at(self, mock_wf, entry_fight_club):
        wl.add_entry(entry_fight_club)
        original = wl.get_entry(550).updated_at
        import time; time.sleep(0.01)
        wl.update_entry(550, note="new note")
        updated = wl.get_entry(550).updated_at
        assert updated >= original


class TestRemoveEntry:
    def test_removes_existing(self, mock_wf, entry_fight_club):
        wl.add_entry(entry_fight_club)
        result = wl.remove_entry(550)
        assert result is True
        assert wl.get_entry(550) is None

    def test_returns_false_for_missing(self, mock_wf):
        result = wl.remove_entry(9999)
        assert result is False


class TestListEntries:
    @pytest.fixture(autouse=True)
    def populate(self, mock_wf, entry_fight_club, entry_breaking_bad):
        wl.add_entry(entry_fight_club)
        wl.add_entry(entry_breaking_bad)
        wl.add_entry(WatchlistEntry.new(807, "movie", "Se7en", "1995", status="watched"))

    def test_returns_all(self, mock_wf):
        entries, total = wl.list_entries()
        assert total == 3

    def test_filter_by_status(self, mock_wf):
        entries, total = wl.list_entries(status="watching")
        assert total == 1
        assert entries[0].title == "Breaking Bad"

    def test_filter_by_media_type(self, mock_wf):
        entries, total = wl.list_entries(media_type="tv")
        assert total == 1
        assert entries[0].media_type == "tv"

    def test_filter_by_search(self, mock_wf):
        entries, total = wl.list_entries(search="fight")
        assert total == 1
        assert entries[0].title == "Fight Club"

    def test_pagination(self, mock_wf):
        entries, total = wl.list_entries(page=1, page_size=2)
        assert total == 3
        assert len(entries) == 2

    def test_second_page(self, mock_wf):
        entries, total = wl.list_entries(page=2, page_size=2)
        assert len(entries) == 1


class TestGetStats:
    def test_stats_calculation(self, mock_wf):
        wl.add_entry(WatchlistEntry.new(550, "movie", "Fight Club", "1999", status="watched"))
        wl.add_entry(WatchlistEntry.new(1396, "tv", "Breaking Bad", "2008", status="watching"))
        wl.add_entry(WatchlistEntry.new(807, "movie", "Se7en", "1995"))

        # Добавляем рейтинг
        wl.update_entry(550, rating=9.5)
        wl.update_entry(807, rating=8.0)

        stats = wl.get_stats()
        assert stats.total == 3
        assert stats.watched == 1
        assert stats.watching == 1
        assert stats.unwatched == 1
        assert stats.movies == 2
        assert stats.tv_shows == 1
        assert stats.watched_percent == pytest.approx(33.3, rel=0.1)
        assert stats.avg_rating == pytest.approx(8.75, rel=0.01)
        assert stats.rated_count == 2


class TestGetWatchedIds:
    def test_returns_watched_ids(self, mock_wf):
        wl.add_entry(WatchlistEntry.new(550, "movie", "Fight Club", "1999", status="watched"))
        wl.add_entry(WatchlistEntry.new(1396, "tv", "Breaking Bad", "2008", status="watching"))
        wl.add_entry(WatchlistEntry.new(807, "movie", "Se7en", "1995"))

        ids = wl.get_watched_ids()
        assert 550 in ids
        assert 1396 not in ids
        assert 807 not in ids
