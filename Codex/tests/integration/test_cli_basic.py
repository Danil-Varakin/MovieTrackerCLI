from __future__ import annotations

from movie_tracker.main import app


def test_cli_version(runner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "MovieTracker CLI Codex" in result.output


def test_cli_init_creates_config(runner, isolated_movie_tracker_home) -> None:
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert (isolated_movie_tracker_home / "settings.toml").exists()


def test_cli_auth_token_and_status(runner) -> None:
    token_result = runner.invoke(app, ["auth", "token", "abcd1234secret"])
    assert token_result.exit_code == 0
    assert "API-ключ сохранён" in token_result.output

    status_result = runner.invoke(app, ["--output", "json", "auth", "status"])
    assert status_result.exit_code == 0
    assert '"authorized": true' in status_result.output


def test_cli_list_watchlist_empty(runner) -> None:
    result = runner.invoke(app, ["list-watchlist"])
    assert result.exit_code == 0
    assert "Ваш список пуст" in result.output
