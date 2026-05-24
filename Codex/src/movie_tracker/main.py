from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from movie_tracker import APP_NAME, __version__
from movie_tracker.cli import auth, cache, details, popular, recommend, search, trending, watchlist
from movie_tracker.cli.state import Runtime
from movie_tracker.config import load_config, write_default_config
from movie_tracker.logging import setup_logging

app = typer.Typer(
    help="MovieTracker CLI Codex — поиск и локальный трекер фильмов/сериалов через Kinopoisk API Unofficial.",
    no_args_is_help=True,
)
app.command("search")(search.search)
app.command("details")(details.details)
app.command("add-watchlist")(watchlist.add_watchlist)
app.command("list-watchlist")(watchlist.list_watchlist)
app.command("rate")(watchlist.rate)
app.command("recommend")(recommend.recommend)
app.command("popular")(popular.popular)
app.command("trending")(trending.trending)
app.add_typer(watchlist.app, name="watchlist")
app.add_typer(auth.app, name="auth")
app.add_typer(cache.app, name="cache")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{APP_NAME} {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    config: Path | None = typer.Option(None, "--config", help="Путь к кастомному settings.toml."),
    output: str | None = typer.Option(None, "--output", help="table | json | csv"),
    no_color: bool = typer.Option(False, "--no-color", help="Отключить цветной вывод."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный debug-вывод."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Минимальный вывод."),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Версия утилиты.",
    ),
) -> None:
    """Глобальные настройки CLI."""
    del version
    cfg = load_config(config)
    cfg.ensure_dirs()
    setup_logging(cfg, verbose=verbose, quiet=quiet)
    selected_output = output or cfg.output_format
    if selected_output not in {"table", "json", "csv"}:
        raise typer.BadParameter("Формат вывода: table | json | csv")
    console = Console(no_color=no_color or not cfg.color_enabled, quiet=quiet)
    ctx.obj = Runtime(cfg, console, selected_output, quiet=quiet)


@app.command("init")
def init(
    ctx: typer.Context,
    force: bool = typer.Option(False, "--force", help="Перезаписать существующий settings.toml."),
) -> None:
    """Создать локальную конфигурацию и каталоги MovieTracker."""
    runtime = ctx.obj if isinstance(ctx.obj, Runtime) else None
    cfg = runtime.config if runtime else load_config()
    path = write_default_config(cfg.source if cfg.source else None, force=force)
    fresh = "перезаписан" if force else "создан или уже существует"
    console = runtime.console if runtime else Console()
    console.print(f"Конфиг {fresh}: {path}", style="green")
    console.print(f"Локальные данные: {cfg.storage_dir}")
