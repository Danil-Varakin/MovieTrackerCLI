"""Кастомные исключения MovieTracker CLI."""

from __future__ import annotations


class MovieTrackerError(Exception):
    """Базовый класс всех исключений MovieTracker."""

    exit_code: int = 1

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthRequired(MovieTrackerError):
    """Действие требует авторизации в Кинопоиске."""

    exit_code = 3

    def __init__(self) -> None:
        super().__init__(
            "Для этого действия нужна авторизация: movie-tracker-claude auth login"
        )


class InvalidAPIKey(MovieTrackerError):
    """Неверный или отсутствующий API ключ."""

    exit_code = 1

    def __init__(self) -> None:
        super().__init__(
            "Ошибка авторизации. Проверьте API ключ: movie-tracker-claude auth token YOUR_KEY"
        )


class ContentNotFound(MovieTrackerError):
    """Контент не найден по ID."""

    exit_code = 2

    def __init__(self, content_id: int, content_type: str = "контент") -> None:
        super().__init__(f"{content_type} с ID {content_id} не найден.")
        self.content_id = content_id


class RateLimitExceeded(MovieTrackerError):
    """Превышен rate limit Кинопоиск API."""

    exit_code = 5

    def __init__(self) -> None:
        super().__init__(
            "Превышен лимит запросов к Кинопоиск API. Попробуйте позже."
        )


class ServiceUnavailable(MovieTrackerError):
    """Сервис Кинопоиск временно недоступен."""

    exit_code = 6

    def __init__(self) -> None:
        super().__init__("Сервис Кинопоиск временно недоступен. Попробуйте позже.")


class NetworkError(MovieTrackerError):
    """Нет подключения к интернету."""

    exit_code = 7

    def __init__(self) -> None:
        super().__init__(
            "Нет подключения к сети. Проверьте интернет-соединение."
        )


class TimeoutError(MovieTrackerError):
    """Превышен таймаут запроса."""

    exit_code = 8

    def __init__(self) -> None:
        super().__init__("Запрос занял слишком долго. Попробуйте позже.")


class InvalidRating(MovieTrackerError):
    """Рейтинг вне допустимого диапазона."""

    exit_code = 9

    def __init__(self) -> None:
        super().__init__(
            "Оценка должна быть от 0.5 до 10.0 (кратно 0.5). Пример: 7.5"
        )


class DuplicateWatchlist(MovieTrackerError):
    """ID уже существует в watchlist."""

    exit_code = 10

    def __init__(self, content_id: int, title: str = "") -> None:
        title_part = f" «{title}»" if title else ""
        super().__init__(
            f"Запись с ID {content_id}{title_part} уже есть в watchlist. "
            f"Используйте: movie-tracker-claude watchlist update {content_id}"
        )
        self.content_id = content_id


class ConfigNotFound(MovieTrackerError):
    """Конфиг-файл не найден."""

    exit_code = 11

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Конфиг-файл не найден: {path}. "
            "Инициализируется конфигурация по умолчанию."
        )


class InvalidContentType(MovieTrackerError):
    """Неверный тип контента."""

    def __init__(self, content_type: str) -> None:
        super().__init__(
            f"Неверный тип контента: '{content_type}'. "
            "Допустимые значения: movie, tv, all"
        )


class StorageError(MovieTrackerError):
    """Ошибка работы с локальным хранилищем."""

    exit_code = 12
