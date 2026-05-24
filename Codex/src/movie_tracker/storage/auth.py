from __future__ import annotations

import json
import os
from contextlib import suppress
from typing import Any

from movie_tracker.config import AppConfig
from movie_tracker.utils.helpers import masked_secret, now_iso


def normalize_api_key(api_key: str) -> str:
    value = api_key.strip().strip("\"'")
    if value.lower().startswith("bearer "):
        value = value[7:].strip()
    return value


class AuthStore:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.path = config.auth_path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def get_api_key(self) -> str:
        data = self.load()
        return normalize_api_key(str(data.get("api_key") or ""))

    def save_api_key(self, api_key: str) -> None:
        clean_key = normalize_api_key(api_key)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "api_key": clean_key,
            "provider": "Kinopoisk API Unofficial",
            "created_at": now_iso(),
        }
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        with suppress(OSError):
            os.chmod(self.path, 0o600)

    def clear(self) -> bool:
        if not self.path.exists():
            return False
        self.path.unlink()
        return True

    def status(self) -> dict[str, Any]:
        data = self.load()
        token = self.get_api_key()
        return {
            "authorized": bool(token),
            "provider": data.get("provider", "Kinopoisk API Unofficial"),
            "created_at": data.get("created_at"),
            "masked_key": masked_secret(token),
            "path": str(self.path),
        }
