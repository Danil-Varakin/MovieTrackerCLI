from __future__ import annotations

import time
from typing import Any

import httpx
from loguru import logger

from movie_tracker.cache import CacheManager
from movie_tracker.config import AppConfig
from movie_tracker.exceptions import AuthorizationError, NetworkError, NotFoundError
from movie_tracker.storage.auth import AuthStore


class KinopoiskClient:
    def __init__(
        self,
        config: AppConfig,
        auth_store: AuthStore | None = None,
        cache: CacheManager | None = None,
    ) -> None:
        self.config = config
        self.auth_store = auth_store or AuthStore(config)
        self.cache = cache or CacheManager(config)

    @property
    def api_key(self) -> str:
        # Explicit environment variables are still the highest priority, but
        # `movie-tracker auth token` must override stale keys left in settings.toml.
        return self.config.env_api_key or self.auth_store.get_api_key() or self.config.api_key

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        ttl_seconds: int = 0,
        cache_namespace: str = "kinopoisk",
    ) -> dict[str, Any] | list[dict[str, Any]]:
        api_key = self.api_key
        if not api_key:
            raise AuthorizationError(
                "Не найден API ключ Kinopoisk. Установите его: movie-tracker auth token YOUR_KEY"
            )

        params = {key: value for key, value in (params or {}).items() if value not in {None, ""}}
        cache_key = CacheManager.make_key(cache_namespace, {"path": path, "params": params})
        if ttl_seconds:
            cached = self.cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for {}", path)
                return cached

        url = f"{self.config.api_base_url}{path}"
        headers = {"X-API-KEY": api_key, "Accept": "application/json"}
        retries = int(self.config.data["api"].get("max_retries", 3))
        backoff = float(self.config.data["api"].get("retry_backoff", 1.0))
        timeout = float(self.config.data["api"].get("timeout", 30))

        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.get(url, params=params, headers=headers)
            except (httpx.ConnectError, httpx.NetworkError) as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(backoff * (2**attempt))
                    continue
                raise NetworkError(
                    "Нет подключения к сети. Проверьте интернет-соединение."
                ) from exc
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < retries:
                    time.sleep(backoff * (2**attempt))
                    continue
                raise NetworkError("Запрос занял слишком долго. Попробуйте позже.") from exc

            logger.debug("GET {} -> {}", response.url, response.status_code)
            if response.status_code in {401, 403}:
                detail = _extract_error_message(response)
                suffix = f" Ответ API: {detail}" if detail else ""
                raise AuthorizationError(
                    f"Ошибка авторизации. Проверьте API ключ Kinopoisk.{suffix}"
                )
            if response.status_code == 404:
                raise NotFoundError("Фильм/сериал с указанным Kinopoisk ID не найден.")
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < retries:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else backoff * (2**attempt)
                    time.sleep(delay)
                    continue
                if response.status_code == 429:
                    raise NetworkError("Превышен лимит Kinopoisk API. Попробуйте позже.")
                raise NetworkError("Сервис Kinopoisk API временно недоступен.")

            response.raise_for_status()
            payload = response.json()
            if ttl_seconds:
                self.cache.set(cache_key, payload, ttl_seconds=ttl_seconds)
            return payload

        raise NetworkError("Запрос к Kinopoisk API не выполнен.") from last_error


def _extract_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip()[:200]
    if isinstance(payload, dict):
        for key in ("message", "error", "errorMessage", "detail"):
            if payload.get(key):
                return str(payload[key])[:200]
    return ""
