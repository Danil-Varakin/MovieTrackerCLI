"""Кинопоиск API — аутентификация и управление сессией."""

from __future__ import annotations

import webbrowser
from typing import Optional

from movie_tracker.api.client import KinopoiskClient as KinopoiskClient


async def create_request_token(client: KinopoiskClient) -> str:
    """Создаёт request token для OAuth flow."""
    data = await client.get("/authentication/token/new")
    return data["request_token"]


async def create_session(client: KinopoiskClient, request_token: str) -> str:
    """Создаёт сессию на основе подтверждённого request token."""
    data = await client.post(
        "/authentication/session/new",
        json={"request_token": request_token},
    )
    return data["session_id"]


async def delete_session(client: KinopoiskClient, session_id: str) -> bool:
    """Инвалидирует сессию на Кинопоиске."""
    data = await client.delete(
        "/authentication/session",
        json={"session_id": session_id},
    )
    return data.get("success", False)


async def get_account_info(client: KinopoiskClient) -> dict:
    """Получить информацию об аккаунте."""
    return await client.get("/account")


def open_auth_browser(request_token: str) -> None:
    """Открывает браузер для авторизации Кинопоиск."""
    url = f"https://www.themoviedb.org/authenticate/{request_token}?redirect_to=movietracker://auth"
    webbrowser.open(url)
