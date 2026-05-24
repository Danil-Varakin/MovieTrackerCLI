from __future__ import annotations

from dataclasses import dataclass

import typer
from rich.console import Console

from movie_tracker.cache import CacheManager
from movie_tracker.config import AppConfig
from movie_tracker.storage.auth import AuthStore
from movie_tracker.storage.watchlist import WatchlistStore


@dataclass
class Runtime:
    config: AppConfig
    console: Console
    output_format: str
    quiet: bool = False

    def auth_store(self) -> AuthStore:
        return AuthStore(self.config)

    def cache(self) -> CacheManager:
        return CacheManager(self.config)

    def watchlist(self) -> WatchlistStore:
        return WatchlistStore(self.config)


def runtime_from_context(ctx: typer.Context) -> Runtime:
    if not isinstance(ctx.obj, Runtime):
        raise typer.Exit(1)
    return ctx.obj
