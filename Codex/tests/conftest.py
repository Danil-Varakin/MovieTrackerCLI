from __future__ import annotations

import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(autouse=True)
def isolated_movie_tracker_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "movie-tracker-home"
    monkeypatch.setenv("MOVIE_TRACKER_HOME", str(home))
    for name in (
        "MOVIE_TRACKER_API__KEY",
        "KINOPOISK_API_KEY",
        "KINOPOISK_UNOFFICIAL_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    return home


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()
