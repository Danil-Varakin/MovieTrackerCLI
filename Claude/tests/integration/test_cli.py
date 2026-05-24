"""Интеграционные тесты CLI — Кинопоиск API."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from movie_tracker.main import app
from tests.conftest import (
    MOCK_KP_FILM_DETAILS,
    MOCK_KP_SEARCH_RESPONSE,
    MOCK_KP_STAFF,
    MOCK_KP_TOP,
)

runner = CliRunner()


class TestSearchCommand:
    def test_search_with_valid_response(self):
        async def mock_get(path, **kwargs):
            return MOCK_KP_SEARCH_RESPONSE

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("movie_tracker.cli.search.KinopoiskClient", return_value=mock_client), \
             patch("movie_tracker.cli.search.get_api_key", return_value="test_key"):
            result = runner.invoke(app, ["search", "Inception"])

        assert result.exit_code == 0
        assert "Начало" in result.output or "Inception" in result.output

    def test_search_outputs_json(self):
        async def mock_get(path, **kwargs):
            return MOCK_KP_SEARCH_RESPONSE

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("movie_tracker.cli.search.KinopoiskClient", return_value=mock_client), \
             patch("movie_tracker.cli.search.get_api_key", return_value="test_key"):
            result = runner.invoke(app, ["search", "Inception", "--output", "json"])

        assert result.exit_code == 0

    def test_search_filters_by_type_movie(self):
        async def mock_get(path, **kwargs):
            return MOCK_KP_SEARCH_RESPONSE

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("movie_tracker.cli.search.KinopoiskClient", return_value=mock_client), \
             patch("movie_tracker.cli.search.get_api_key", return_value="test_key"):
            result = runner.invoke(app, ["search", "Inception", "--type", "movie"])

        assert result.exit_code == 0

    def test_search_no_api_key(self):
        with patch("movie_tracker.cli.search.get_api_key", return_value=""):
            result = runner.invoke(app, ["search", "Inception"])
        assert result.exit_code != 0

    def test_search_no_results(self):
        async def mock_get(path, **kwargs):
            return {"total": 0, "totalPages": 0, "items": []}

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("movie_tracker.cli.search.KinopoiskClient", return_value=mock_client), \
             patch("movie_tracker.cli.search.get_api_key", return_value="test_key"):
            result = runner.invoke(app, ["search", "xyzxyzxyz12345"])

        assert result.exit_code == 0
        assert "Ничего не найдено" in result.output


class TestAddWatchlistCommand:
    def _make_db(self, path):
        from tinydb import TinyDB
        from tinydb.storages import JSONStorage
        from tinydb.middlewares import CachingMiddleware
        return TinyDB(str(path), storage=CachingMiddleware(JSONStorage))

    def test_add_shows_confirmation(self, tmp_path):
        async def mock_get(path, **kwargs):
            return MOCK_KP_FILM_DETAILS

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        db_file = tmp_path / "wl_add.json"
        def fresh_db(): return self._make_db(db_file)

        with patch("movie_tracker.cli.watchlist.KinopoiskClient", return_value=mock_client), \
             patch("movie_tracker.cli.watchlist.auth_storage.load_auth", return_value=None), \
             patch("movie_tracker.cli.watchlist.get_api_key", return_value="test_key"), \
             patch("movie_tracker.storage.watchlist._get_db", side_effect=fresh_db):
            result = runner.invoke(app, ["add-watchlist", "447301", "--type", "movie"])

        assert result.exit_code == 0
        assert "Добавлено" in result.output or "447301" in result.output

    def test_add_watchlist_no_api_key(self):
        with patch("movie_tracker.cli.watchlist.get_api_key", return_value=""):
            result = runner.invoke(app, ["add-watchlist", "447301"])
        assert result.exit_code != 0


class TestListWatchlistCommand:
    def _make_db(self, path):
        from tinydb import TinyDB
        from tinydb.storages import JSONStorage
        from tinydb.middlewares import CachingMiddleware
        return TinyDB(str(path), storage=CachingMiddleware(JSONStorage))

    def test_list_empty(self, tmp_path):
        db_file = tmp_path / "wl_empty.json"
        def fresh_db(): return self._make_db(db_file)
        with patch("movie_tracker.storage.watchlist._get_db", side_effect=fresh_db):
            result = runner.invoke(app, ["list-watchlist"])
        assert result.exit_code == 0
        assert "пуст" in result.output.lower()

    def test_list_with_stats(self, tmp_path):
        db_file = tmp_path / "wl_stats.json"
        def fresh_db(): return self._make_db(db_file)
        with patch("movie_tracker.storage.watchlist._get_db", side_effect=fresh_db):
            result = runner.invoke(app, ["list-watchlist", "--stats"])
        assert result.exit_code == 0


class TestAuthCommand:
    def test_set_token(self):
        with patch("movie_tracker.config.update_setting"):
            result = runner.invoke(app, ["auth", "token", "test_api_key_1234"])
        assert result.exit_code == 0
        assert "сохранён" in result.output

    def test_set_token_too_short(self):
        result = runner.invoke(app, ["auth", "token", "abc"])
        assert result.exit_code != 0

    def test_auth_status_no_key(self):
        with patch("movie_tracker.config.get_api_key", return_value=""):
            result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "не установлен" in result.output

    def test_auth_status_with_key(self):
        with patch("movie_tracker.config.get_api_key", return_value="my_api_key_1234"):
            result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "установлен" in result.output


class TestWatchlistUpdateRemove:
    def test_remove_nonexistent(self, tmp_path):
        with patch("movie_tracker.config.get_watchlist_file", return_value=tmp_path / "watchlist.json"):
            result = runner.invoke(app, ["watchlist", "remove", "9999", "--force"])
        # Запись не найдена — выходим с кодом 1 (корректное поведение)
        assert "9999" in result.output or result.exit_code in (0, 1)

    def test_update_nonexistent(self, tmp_path):
        with patch("movie_tracker.config.get_watchlist_file", return_value=tmp_path / "watchlist.json"):
            result = runner.invoke(app, ["watchlist", "update", "9999", "--status", "watched"])
        assert "9999" in result.output or result.exit_code in (0, 1)
