"""Управление конфигурацией MovieTracker CLI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dynaconf import Dynaconf

# Директория конфигурации по умолчанию
DEFAULT_CONFIG_DIR = Path.home() / ".movie-tracker"
DEFAULT_SETTINGS_FILE = DEFAULT_CONFIG_DIR / "settings.toml"

# Путь к настройкам по умолчанию (из пакета)
_PACKAGE_SETTINGS = Path(__file__).parent.parent.parent / "settings.toml"


def _ensure_config_dir() -> None:
    """Создаёт директорию конфигурации если не существует."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (DEFAULT_CONFIG_DIR / "cache").mkdir(exist_ok=True)


def _init_user_settings() -> None:
    """Инициализирует пользовательский settings.toml если не существует."""
    _ensure_config_dir()
    if not DEFAULT_SETTINGS_FILE.exists() and _PACKAGE_SETTINGS.exists():
        import shutil
        shutil.copy(_PACKAGE_SETTINGS, DEFAULT_SETTINGS_FILE)


_init_user_settings()

settings = Dynaconf(
    envvar_prefix="MOVIE_TRACKER",
    settings_files=[
        str(_PACKAGE_SETTINGS),
        str(DEFAULT_SETTINGS_FILE),
        ".env",
    ],
    environments=False,
    load_dotenv=True,
)


def get_api_key() -> str:
    """Возвращает Кинопоиск API ключ из конфига или переменных окружения."""
    key = settings.get("API__KEY", "") or os.environ.get("Кинопоиск_API_KEY", "")
    return str(key)


def get_base_url() -> str:
    """Возвращает базовый URL API."""
    return str(settings.get("API__BASE_URL", "https://kinopoiskapiunofficial.tech/api"))


def get_timeout() -> int:
    """Возвращает таймаут HTTP-запросов в секундах."""
    return int(settings.get("API__TIMEOUT", 30))


def get_max_retries() -> int:
    """Возвращает максимальное количество повторных попыток."""
    return int(settings.get("API__MAX_RETRIES", 3))


def get_retry_backoff() -> float:
    """Возвращает начальный интервал backoff в секундах."""
    return float(settings.get("API__RETRY_BACKOFF", 1.0))


def get_output_format() -> str:
    """Возвращает формат вывода: table | json | csv."""
    return str(settings.get("OUTPUT__FORMAT", "table"))


def get_language() -> str:
    """Возвращает язык ответов Кинопоиск."""
    return str(settings.get("OUTPUT__LANGUAGE", "ru-RU"))


def get_region() -> str:
    """Возвращает регион для локализации."""
    return str(settings.get("OUTPUT__REGION", "RU"))


def get_color() -> bool:
    """Возвращает флаг цветного вывода."""
    return bool(settings.get("OUTPUT__COLOR", True))


def get_page_size() -> int:
    """Возвращает количество результатов на странице."""
    return int(settings.get("OUTPUT__PAGE_SIZE", 10))


def get_cache_enabled() -> bool:
    """Возвращает флаг включения кэша."""
    return bool(settings.get("CACHE__ENABLED", True))


def get_cache_dir() -> Path:
    """Возвращает директорию кэша."""
    raw = str(settings.get("CACHE__DIR", "~/.movie-tracker/cache"))
    return Path(raw).expanduser()


def get_cache_max_size() -> int:
    """Возвращает максимальный размер кэша в байтах."""
    mb = int(settings.get("CACHE__MAX_SIZE_MB", 100))
    return mb * 1024 * 1024


def get_storage_dir() -> Path:
    """Возвращает директорию локального хранилища."""
    raw = str(settings.get("STORAGE__DIR", "~/.movie-tracker"))
    return Path(raw).expanduser()


def get_watchlist_file() -> Path:
    """Возвращает путь к файлу watchlist."""
    storage_dir = get_storage_dir()
    filename = str(settings.get("STORAGE__WATCHLIST_FILE", "watchlist.json"))
    return storage_dir / filename


def get_log_level() -> str:
    """Возвращает уровень логирования."""
    return str(settings.get("LOGGING__LEVEL", "WARNING"))


def get_log_file() -> Path:
    """Возвращает путь к файлу логов."""
    raw = str(settings.get("LOGGING__FILE", "~/.movie-tracker/movie-tracker.log"))
    return Path(raw).expanduser()


def get_log_rotation() -> str:
    """Возвращает настройку ротации логов."""
    return str(settings.get("LOGGING__ROTATION", "10 MB"))


def get_log_retention() -> str:
    """Возвращает срок хранения логов."""
    return str(settings.get("LOGGING__RETENTION", "30 days"))


def get_auth_file() -> Path:
    """Возвращает путь к файлу аутентификации."""
    return get_storage_dir() / "auth.json"


def update_setting(key: str, value: Any, config_path: Path | None = None) -> None:
    """Обновляет настройку в пользовательском settings.toml."""
    import tomllib
    import tomli_w  # type: ignore

    target = config_path or DEFAULT_SETTINGS_FILE
    _ensure_config_dir()

    if target.exists():
        with open(target, "rb") as f:
            data = tomllib.load(f)
    else:
        data = {}

    # Парсим ключ вида "api.key" → вложенный dict
    parts = key.lower().split(".")
    current = data
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value

    with open(target, "wb") as f:
        tomli_w.dump(data, f)
