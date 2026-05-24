from __future__ import annotations

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.search import search_media
from movie_tracker.cache import CacheManager
from movie_tracker.config import load_config
from movie_tracker.storage.auth import AuthStore


def test_search_media_normalizes_keyword_response(httpx_mock, monkeypatch) -> None:
    monkeypatch.setenv("MOVIE_TRACKER_API__KEY", "test-token")
    httpx_mock.add_response(
        json={
            "films": [
                {
                    "filmId": 301,
                    "nameRu": "Матрица",
                    "type": "FILM",
                    "year": "1999",
                    "rating": "8.5",
                    "genres": [{"genre": "фантастика"}],
                    "countries": [{"country": "США"}],
                }
            ]
        }
    )

    config = load_config()
    client = KinopoiskClient(config, AuthStore(config), CacheManager(config))
    items = search_media(client, query="Матрица", per_page=5)

    assert items[0]["id"] == 301
    assert items[0]["title"] == "Матрица"
    assert items[0]["media_type"] == "movie"


def test_saved_auth_token_overrides_stale_settings_key(httpx_mock) -> None:
    httpx_mock.add_response(json={"ok": True})
    config = load_config()
    config.data["api"]["key"] = "stale-settings-key"
    auth_store = AuthStore(config)
    auth_store.save_api_key("saved-auth-key")

    client = KinopoiskClient(config, auth_store, CacheManager(config))
    payload = client.get("/v2.2/films/301")

    request = httpx_mock.get_request()
    assert payload == {"ok": True}
    assert request.headers["X-API-KEY"] == "saved-auth-key"


def test_env_token_overrides_saved_auth_token(httpx_mock, monkeypatch) -> None:
    monkeypatch.setenv("MOVIE_TRACKER_API__KEY", "env-key")
    httpx_mock.add_response(json={"ok": True})
    config = load_config()
    auth_store = AuthStore(config)
    auth_store.save_api_key("saved-auth-key")

    client = KinopoiskClient(config, auth_store, CacheManager(config))
    client.get("/v2.2/films/301")

    request = httpx_mock.get_request()
    assert request.headers["X-API-KEY"] == "env-key"
