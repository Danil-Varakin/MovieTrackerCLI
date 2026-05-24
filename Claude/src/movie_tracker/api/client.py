"""HTTP-клиент для Кинопоиск Unofficial API (kinopoiskapiunofficial.tech)."""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Optional

import httpx
from loguru import logger

from movie_tracker.config import (
    get_api_key,
    get_max_retries,
    get_retry_backoff,
    get_timeout,
)
from movie_tracker.exceptions import (
    ContentNotFound,
    InvalidAPIKey,
    NetworkError,
    RateLimitExceeded,
    ServiceUnavailable,
)
from movie_tracker.exceptions import TimeoutError as TrackerTimeoutError

# Базовый URL API — никогда не меняется
KINOPOISK_BASE_URL = "https://kinopoiskapiunofficial.tech"


class KinopoiskClient:
    """
    Асинхронный клиент для kinopoiskapiunofficial.tech.

    Все endpoint-ы используются как абсолютные пути:
      /api/v2.2/films          — поиск
      /api/v2.2/films/{id}    — детали
      /api/v1/staff            — состав
      /api/v1/reviews          — рецензии
      /api/v2.2/films/top      — топы
    Заголовок авторизации: X-API-KEY: <token>
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or get_api_key()
        self.timeout = get_timeout()
        self.max_retries = get_max_retries()
        self.backoff = get_retry_backoff()
        self._client: Optional[httpx.AsyncClient] = None

    def _build_client(self) -> httpx.AsyncClient:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["X-API-KEY"] = self.api_key

        timeout = httpx.Timeout(
            connect=15.0,
            read=max(self.timeout, 30.0),
            write=10.0,
            pool=5.0,
        )

        # НЕ указываем base_url — используем абсолютные URL в каждом запросе
        # НЕ указываем прокси — API работает в России напрямую
        return httpx.AsyncClient(
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
            http2=False,
        )

    async def __aenter__(self) -> "KinopoiskClient":
        self._client = self._build_client()
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> Any:
        if not self._client:
            raise RuntimeError("Клиент не инициализирован. Используйте async with.")

        # Строим абсолютный URL: base + path
        # path должен начинаться с /api/...
        url = f"{KINOPOISK_BASE_URL}{path}"

        # Убираем None из параметров
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        attempt = 0
        last_error: Exception = RuntimeError("Unknown error")

        while attempt <= self.max_retries:
            start = time.monotonic()
            try:
                response = await self._client.request(
                    method, url, params=clean_params, json=json_data
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)
                logger.debug(f"{method} {url} → {response.status_code} ({elapsed_ms}ms)")

                if response.status_code in (200, 201):
                    return response.json()
                if response.status_code in (401, 403):
                    raise InvalidAPIKey()
                if response.status_code == 404:
                    raise ContentNotFound(0)
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 5))
                    wait = max(retry_after, self.backoff * (2 ** attempt)) + random.uniform(0, 0.5)
                    logger.warning(f"Rate limit (429). Жду {wait:.1f}s")
                    if attempt < self.max_retries:
                        await asyncio.sleep(wait)
                        attempt += 1
                        continue
                    raise RateLimitExceeded()
                if response.status_code >= 500:
                    last_error = ServiceUnavailable()
                    if attempt < self.max_retries:
                        await asyncio.sleep(self.backoff * (2 ** attempt))
                        attempt += 1
                        continue
                    raise last_error
                # Другие коды — возвращаем JSON как есть
                return response.json()

            except (InvalidAPIKey, ContentNotFound, RateLimitExceeded, ServiceUnavailable):
                raise
            except httpx.ConnectError as e:
                last_error = NetworkError()
                logger.error(f"Ошибка подключения к {url}: {e}")
                if attempt < self.max_retries:
                    wait = self.backoff * (2 ** attempt)
                    logger.warning(f"Повтор через {wait:.1f}s (попытка {attempt + 1}/{self.max_retries})")
                    await asyncio.sleep(wait)
                    attempt += 1
                    continue
                raise NetworkError() from e
            except httpx.TimeoutException as e:
                last_error = TrackerTimeoutError()
                logger.warning(f"Таймаут запроса к {url} (попытка {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.backoff * (2 ** attempt))
                    attempt += 1
                    continue
                raise TrackerTimeoutError() from e
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {e}")
                raise

        raise last_error

    async def get(self, path: str, **params: Any) -> Any:
        """GET-запрос. path должен начинаться с /api/..."""
        return await self._request("GET", path, params=params if params else None)

    async def post(self, path: str, json_data: Optional[dict] = None, **params: Any) -> Any:
        """POST-запрос."""
        return await self._request("POST", path, params=params if params else None, json_data=json_data)


# Алиас для обратной совместимости
TMDBClient = KinopoiskClient


def run_async(coro: Any) -> Any:
    return asyncio.run(coro)
