from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "api": {
        "key": "",
        "base_url": "https://kinopoiskapiunofficial.tech/api",
        "timeout": 30,
        "max_retries": 3,
        "retry_backoff": 1.0,
    },
    "output": {
        "format": "table",
        "language": "ru-RU",
        "region": "RU",
        "color": True,
        "page_size": 10,
    },
    "cache": {
        "enabled": True,
        "dir": "~/.movie-tracker/cache",
        "max_size_mb": 100,
    },
    "storage": {
        "dir": "~/.movie-tracker",
        "watchlist_file": "watchlist.json",
        "auth_file": "auth.json",
    },
    "logging": {
        "level": "WARNING",
        "file": "~/.movie-tracker/movie-tracker.log",
        "rotation": "10 MB",
        "retention": "30 days",
    },
}


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on", "да"}


def _apply_env(config: dict[str, Any]) -> dict[str, Any]:
    env_map: dict[str, tuple[str, str, type[Any]]] = {
        "MOVIE_TRACKER_API__KEY": ("api", "key", str),
        "KINOPOISK_API_KEY": ("api", "key", str),
        "KINOPOISK_UNOFFICIAL_API_KEY": ("api", "key", str),
        "MOVIE_TRACKER_API__BASE_URL": ("api", "base_url", str),
        "MOVIE_TRACKER_API__TIMEOUT": ("api", "timeout", int),
        "MOVIE_TRACKER_OUTPUT__FORMAT": ("output", "format", str),
        "MOVIE_TRACKER_OUTPUT__LANGUAGE": ("output", "language", str),
        "MOVIE_TRACKER_OUTPUT__REGION": ("output", "region", str),
        "MOVIE_TRACKER_OUTPUT__COLOR": ("output", "color", bool),
        "MOVIE_TRACKER_CACHE__ENABLED": ("cache", "enabled", bool),
        "MOVIE_TRACKER_CACHE__DIR": ("cache", "dir", str),
        "MOVIE_TRACKER_STORAGE__DIR": ("storage", "dir", str),
        "MOVIE_TRACKER_LOGGING__LEVEL": ("logging", "level", str),
    }
    for env_name, (section, key, value_type) in env_map.items():
        if env_name not in os.environ:
            continue
        raw = os.environ[env_name]
        if value_type is bool:
            value: Any = _as_bool(raw)
        else:
            value = value_type(raw)
        config.setdefault(section, {})[key] = value
        if section == "api" and key == "key":
            config.setdefault("_runtime", {})["api_key_from_env"] = str(value).strip()

    if home := os.environ.get("MOVIE_TRACKER_HOME"):
        config.setdefault("storage", {})["dir"] = home
        config.setdefault("cache", {})["dir"] = str(Path(home) / "cache")
        config.setdefault("logging", {})["file"] = str(Path(home) / "movie-tracker.log")
    return config


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def _expand(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


@dataclass(frozen=True)
class AppConfig:
    data: dict[str, Any]
    source: Path | None = None

    @property
    def storage_dir(self) -> Path:
        return _expand(self.data["storage"]["dir"])

    @property
    def watchlist_path(self) -> Path:
        return self.storage_dir / self.data["storage"]["watchlist_file"]

    @property
    def auth_path(self) -> Path:
        return self.storage_dir / self.data["storage"]["auth_file"]

    @property
    def cache_dir(self) -> Path:
        return _expand(self.data["cache"]["dir"])

    @property
    def log_path(self) -> Path:
        return _expand(self.data["logging"]["file"])

    @property
    def api_key(self) -> str:
        return str(self.data["api"].get("key", "")).strip()

    @property
    def env_api_key(self) -> str:
        return str(self.data.get("_runtime", {}).get("api_key_from_env", "")).strip()

    @property
    def api_base_url(self) -> str:
        return str(self.data["api"]["base_url"]).rstrip("/")

    @property
    def output_format(self) -> str:
        return str(self.data["output"]["format"])

    @property
    def color_enabled(self) -> bool:
        return bool(self.data["output"].get("color", True))

    def ensure_dirs(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)


def user_config_path() -> Path:
    home = os.environ.get("MOVIE_TRACKER_HOME")
    if home:
        return _expand(Path(home) / "settings.toml")
    return _expand("~/.movie-tracker/settings.toml")


def load_config(config_path: str | Path | None = None) -> AppConfig:
    config = deepcopy(DEFAULT_CONFIG)
    selected_path = Path(config_path).expanduser() if config_path else user_config_path()

    if selected_path.exists():
        config = _deep_merge(config, _read_toml(selected_path))

    config = _apply_env(config)
    return AppConfig(config, selected_path)


def default_config_text() -> str:
    return """[api]
key = ""
base_url = "https://kinopoiskapiunofficial.tech/api"
timeout = 30
max_retries = 3
retry_backoff = 1.0

[output]
format = "table"
language = "ru-RU"
region = "RU"
color = true
page_size = 10

[cache]
enabled = true
dir = "~/.movie-tracker/cache"
max_size_mb = 100

[storage]
dir = "~/.movie-tracker"
watchlist_file = "watchlist.json"
auth_file = "auth.json"

[logging]
level = "WARNING"
file = "~/.movie-tracker/movie-tracker.log"
rotation = "10 MB"
retention = "30 days"
"""


def write_default_config(path: Path | None = None, *, force: bool = False) -> Path:
    target = path or user_config_path()
    target = target.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        return target
    target.write_text(default_config_text(), encoding="utf-8")
    return target
