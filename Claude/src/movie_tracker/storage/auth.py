"""Хранение токенов аутентификации."""

from __future__ import annotations

import json
import os
import stat
from typing import Optional

from movie_tracker.config import get_auth_file
from movie_tracker.models import AuthInfo


def save_auth(auth: AuthInfo) -> None:
    """Сохраняет данные авторизации в auth.json с правами 600."""
    auth_file = get_auth_file()
    auth_file.parent.mkdir(parents=True, exist_ok=True)

    with open(auth_file, "w", encoding="utf-8") as f:
        json.dump(auth.to_dict(), f, ensure_ascii=False, indent=2)

    # Устанавливаем права 600 (только владелец может читать/писать)
    try:
        os.chmod(auth_file, stat.S_IRUSR | stat.S_IWUSR)
    except (OSError, NotImplementedError):
        pass  # На Windows права не применяются


def load_auth() -> Optional[AuthInfo]:
    """Загружает данные авторизации. Возвращает None если не авторизован."""
    auth_file = get_auth_file()
    if not auth_file.exists():
        return None
    try:
        with open(auth_file, encoding="utf-8") as f:
            data = json.load(f)
        return AuthInfo.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None


def delete_auth() -> bool:
    """Удаляет файл авторизации. Возвращает True если файл существовал."""
    auth_file = get_auth_file()
    if auth_file.exists():
        auth_file.unlink()
        return True
    return False


def is_authenticated() -> bool:
    """Проверяет наличие данных авторизации."""
    return load_auth() is not None


def get_session_id() -> Optional[str]:
    """Возвращает session_id если авторизован."""
    auth = load_auth()
    return auth.session_id if auth else None


def get_account_id() -> Optional[int]:
    """Возвращает account_id если авторизован."""
    auth = load_auth()
    return auth.account_id if auth else None
