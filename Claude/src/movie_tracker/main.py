"""MovieTracker CLI — точка входа."""

from __future__ import annotations

import sys
from typing import Optional

import typer
from loguru import logger
from rich.console import Console

from movie_tracker.config import get_log_file, get_log_level, get_log_retention, get_log_rotation

__version__ = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────────

logger.remove()  # Убираем дефолтный хэндлер

_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
    "<level>{message}</level>"
)

_LOG_JSON_FORMAT = (
    '{{"timestamp": "{time:YYYY-MM-DDTHH:mm:ss.SSS}Z", '
    '"level": "{level}", '
    '"message": "{message}", '
    '"name": "{name}"}}'
)

def _setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    log_level = "DEBUG" if verbose else ("ERROR" if quiet else get_log_level())

    # Консольный хэндлер
    if not quiet:
        logger.add(
            sys.stderr,
            level=log_level,
            format=_LOG_FORMAT,
            colorize=True,
            filter=lambda record: record["level"].no >= logger.level(log_level).no,
        )

    # Файловый хэндлер (JSON)
    try:
        log_file = get_log_file()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_file),
            level="DEBUG",
            format=_LOG_JSON_FORMAT,
            rotation=get_log_rotation(),
            retention=get_log_retention(),
            serialize=False,
        )
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────
# Main Typer App
# ─────────────────────────────────────────────────────────────

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}

app = typer.Typer(
    name="movie-tracker-claude",
    help=(
        "[bold cyan]MovieTracker CLI[/bold cyan] — поиск, отслеживание и анализ "
        "фильмов и сериалов через Кинопоиск API.\n\n"
        "Начало работы: [bold]movie-tracker-claude auth token YOUR_KINOPOISK_KEY[/bold]\n"
        "Первый поиск:  [bold]movie-tracker-claude search 'Inception'[/bold]"
    ),
    add_completion=False,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
    pretty_exceptions_short=True,
    context_settings=CONTEXT_SETTINGS,
)

console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold]MovieTracker CLI[/bold] v{__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False, "--version", callback=version_callback, is_eager=True,
        help="Показать версию и выйти."
    ),
    config: Optional[str] = typer.Option(
        None, "--config", help="Путь к кастомному конфиг-файлу"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Формат вывода: table | json | csv",
        envvar="MOVIE_TRACKER_OUTPUT"
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Отключить цветной вывод"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Подробный вывод"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Минимальный вывод"),
) -> None:
    """MovieTracker CLI — ваш личный кинотрекер в терминале."""
    _setup_logging(verbose=verbose, quiet=quiet)

    if no_color:
        import os
        os.environ["NO_COLOR"] = "1"


# ─────────────────────────────────────────────────────────────
# Регистрация команд
# ─────────────────────────────────────────────────────────────

# search
from movie_tracker.cli.search import app as _search_app, search_cmd
app.command("search", help="🔍 Поиск фильмов и сериалов.")(search_cmd)

# details
from movie_tracker.cli.details import app as _details_app, details_cmd
app.command("details", help="📄 Детальная информация о фильме или сериале.")(details_cmd)

# watchlist add / list
from movie_tracker.cli.watchlist import add_watchlist, list_watchlist, watchlist_app
app.command("add-watchlist", help="➕ Добавить фильм/сериал в список просмотра.")(add_watchlist)
app.command("list-watchlist", help="📋 Просмотреть свой список просмотра.")(list_watchlist)
app.add_typer(watchlist_app, name="watchlist", help="🗂  Управление записями watchlist (update, remove).")

# rate
from movie_tracker.cli.actions import (
    popular_app,
    rate_app,
    recommend_app,
    trending_app,
    rate_cmd,
    popular_cmd,
    trending_cmd,
    recommend_cmd,
)
app.command("rate", help="⭐ Оценить фильм или сериал.")(rate_cmd)
app.command("popular", help="🔥 Популярный контент.")(popular_cmd)
app.command("trending", help="📈 Трендовый контент.")(trending_cmd)
app.command("recommend", help="🎯 Персональные рекомендации.")(recommend_cmd)

# auth
from movie_tracker.cli.auth import app as auth_app
app.add_typer(auth_app, name="auth", help="🔐 Аутентификация и управление API ключом.")


# ─────────────────────────────────────────────────────────────
# Cache management
# ─────────────────────────────────────────────────────────────

cache_app = typer.Typer(help="💾 Управление кэшем запросов.")
app.add_typer(cache_app, name="cache")


@cache_app.command("clear")
def cache_clear(
    older_than: Optional[int] = typer.Option(
        None, "--older-than", help="Удалить записи старше N часов"
    ),
) -> None:
    """Очистить кэш запросов к Кинопоиск API."""
    from movie_tracker.cache.manager import cache_clear as _clear
    count = _clear(older_than)
    if older_than:
        console.print(f"[green]✓[/green] Кэш очищен (записей старше {older_than}ч удалено).")
    else:
        console.print(f"[green]✓[/green] Кэш полностью очищен.")


@cache_app.command("stats")
def cache_stats() -> None:
    """Статистика использования кэша."""
    from movie_tracker.cache.manager import get_cache
    cache = get_cache()
    size_mb = cache.volume() / (1024 * 1024)
    count = len(cache)
    console.print(f"[bold]💾 Кэш:[/bold] {count} записей, {size_mb:.2f} МБ")


# ─────────────────────────────────────────────────────────────
# Init command
# ─────────────────────────────────────────────────────────────

@app.command("init")
def init_cmd() -> None:
    """Инициализировать конфигурацию MovieTracker CLI."""
    from movie_tracker.config import DEFAULT_CONFIG_DIR, DEFAULT_SETTINGS_FILE, _ensure_config_dir
    _ensure_config_dir()

    console.print(f"[green]✓[/green] Директория конфигурации: [bold]{DEFAULT_CONFIG_DIR}[/bold]")
    console.print(f"[green]✓[/green] Файл настроек: [bold]{DEFAULT_SETTINGS_FILE}[/bold]")
    console.print()
    console.print("Следующий шаг — установите API ключ Кинопоиска:")
    console.print("  [bold]movie-tracker-claude auth token YOUR_KINOPOISK_KEY[/bold]")
    console.print()
    console.print("Получить API ключ: [link=https://kinopoiskapiunofficial.tech]kinopoiskapiunofficial.tech[/link]")


@app.command("check")
def check_cmd() -> None:
    """🔧 Диагностика: проверить API ключ и реальное подключение к Кинопоиску."""
    import asyncio
    from movie_tracker.api.client import KinopoiskClient
    from movie_tracker.config import get_api_key

    console.print("[bold]🔧 Диагностика MovieTracker CLI[/bold]\n")

    # 1. API ключ
    api_key = get_api_key()
    if api_key:
        console.print(f"[green]✓[/green] API ключ: [dim]{api_key[:4]}***{api_key[-4:]}[/dim]")
    else:
        console.print("[red]✗[/red] API ключ не установлен")
        console.print("  Выполните: [bold]movie-tracker-claude auth token YOUR_KEY[/bold]")
        console.print("  Получить ключ: [link=https://kinopoiskapiunofficial.tech]kinopoiskapiunofficial.tech[/link]")
        raise typer.Exit(1)

    # 2. Реальный тест через KinopoiskClient (тот же клиент, что используют команды)
    console.print("\n[dim]→ Отправляю тестовый запрос к kinopoiskapiunofficial.tech...[/dim]")

    async def _test() -> tuple[bool, str]:
        try:
            async with KinopoiskClient(api_key=api_key) as client:
                # GET /api/v2.2/films/top?type=TOP_100_POPULAR_FILMS&page=1
                data = await client.get(
                    "/api/v2.2/films/top",
                    type="TOP_100_POPULAR_FILMS",
                    page=1,
                )
                films = data.get("films", [])
                count = len(films)
                first = films[0].get("nameRu", "") if films else ""
                return True, f"получено {count} фильмов, первый: «{first}»"
        except Exception as e:
            return False, str(e)

    ok, detail = asyncio.run(_test())
    if ok:
        console.print(f"[green]✓[/green] Подключение [bold green]успешно[/bold green] — {detail}")
        console.print("\n[bold]Готово! Попробуйте:[/bold]")
        console.print("  movie-tracker-claude search 'Интерстеллар'")
        console.print("  movie-tracker-claude popular --type movie")
        console.print("  movie-tracker-claude trending --window top250")
    else:
        console.print(f"[red]✗[/red] Ошибка: {detail}")
        console.print("\n[bold]Возможные причины:[/bold]")
        console.print("  • Неверный API ключ → проверьте на kinopoiskapiunofficial.tech")
        console.print("  • Нет интернета → проверьте соединение")
        console.print("  • Превышен лимит запросов (500/сутки для бесплатного ключа)")


if __name__ == "__main__":
    app()
