"""CLI команды watchlist: add-watchlist, list-watchlist, watchlist update/remove."""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.details import get_movie_details, get_tv_details
from movie_tracker.config import get_api_key
from movie_tracker.exceptions import DuplicateWatchlist, MovieTrackerError
from movie_tracker.formatters.table import (
    error,
    info,
    print_watchlist,
    success,
    warning,
)
from movie_tracker.models import WatchlistEntry
from movie_tracker.storage import auth as auth_storage
from movie_tracker.storage import watchlist as wl_storage
from movie_tracker.utils.validators import (
    parse_tags,
    validate_limit,
    validate_page,
    validate_rating,
)

app = typer.Typer()
watchlist_app = typer.Typer(
    help="🗂  Обновление и удаление записей watchlist.",
    no_args_is_help=True,
)
console = Console()


async def _fetch_title(
    film_id: int, content_type: Optional[str]
) -> tuple[str, str, str]:
    """Возвращает (media_type, title, year) через API."""
    api_key = get_api_key()
    if not api_key:
        raise MovieTrackerError("API ключ не установлен.")

    async with KinopoiskClient(api_key=api_key) as client:
        try:
            data = await get_movie_details(client, film_id)
            if isinstance(data, dict):
                kp_type = data.get("type", "FILM")
                tv_types = {"TV_SERIES", "TV_SHOW", "MINI_SERIES"}
                media = "tv" if kp_type in tv_types else "movie"
                title = data.get("nameRu") or data.get("nameEn") or data.get("nameOriginal") or f"ID:{film_id}"
                year = str(data.get("year", "—"))
                return media, title, year
            else:
                return "movie", str(data), "—"
        except MovieTrackerError:
            raise
        except Exception:
            raise MovieTrackerError(f"Контент с ID {film_id} не найден.")


@app.command("add-watchlist")
def add_watchlist(
    film_id: int = typer.Argument(
        ...,
        help=(
            "ID фильма или сериала на Кинопоиске. "
            "Узнать ID: movie-tracker-claude search <название> → смотрите колонку ID"
        ),
    ),
    content_type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="Тип контента: movie (фильм) | tv (сериал). Определяется автоматически.",
    ),
    status: str = typer.Option(
        "unwatched", "--status", "-s",
        help=(
            "Начальный статус записи:\n"
            "  unwatched — не смотрел (по умолчанию)\n"
            "  watching  — смотрю сейчас\n"
            "  watched   — уже посмотрел"
        ),
    ),
    priority: int = typer.Option(
        3, "--priority",
        help="Приоритет просмотра от 1 (низкий) до 5 (высокий). По умолчанию: 3",
        min=1, max=5,
    ),
    note: Optional[str] = typer.Option(
        None, "--note", "-n",
        help="Личная заметка к записи. Пример: --note 'Посмотреть с друзьями'",
    ),
    tags: Optional[str] = typer.Option(
        None, "--tags",
        help="Теги через запятую. Пример: --tags 'нолан,фантастика,обязательно'",
    ),
) -> None:
    """➕ Добавить фильм или сериал в список просмотра.

    Находит фильм по ID, запрашивает его данные с Кинопоиска
    и сохраняет в локальный watchlist.

    Узнать ID фильма: movie-tracker-claude search 'название'

    Примеры:
      movie-tracker-claude add-watchlist 447301
      movie-tracker-claude add-watchlist 447301 --status watching --priority 5
      movie-tracker-claude add-watchlist 447301 --note 'Посмотреть с друзьями'
      movie-tracker-claude add-watchlist 447301 --tags 'нолан,мастхэв'
    """
    api_key = get_api_key()
    if not api_key:
        error("API ключ не установлен. Выполните: movie-tracker-claude auth token YOUR_KEY")
        raise typer.Exit(1)

    if status not in ("watched", "unwatched", "watching"):
        error("Статус должен быть: watched | unwatched | watching")
        raise typer.Exit(1)

    existing = wl_storage.get_entry(film_id)
    if existing:
        warning(f"ID {film_id} «{existing.title}» уже в списке.")
        update = typer.confirm("Обновить запись?", default=False)
        if not update:
            console.print("[dim]Отменено.[/dim]")
            raise typer.Exit(0)
        wl_storage.update_entry(film_id, status=status, priority=priority, note=note)
        success(f"Запись обновлена: {existing.title} (ID: {film_id})")
        return

    resolved_type, title, year = asyncio.run(_fetch_title(film_id, content_type))

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    entry = WatchlistEntry(
        film_id=film_id,
        media_type=resolved_type,
        title=title,
        year=year,
        status=status,
        priority=priority,
        rating=None,
        note=note or "",
        tags=parse_tags(tags),
        added_at=now,
        updated_at=now,
    )

    wl_storage.add_entry(entry)
    success(f"Добавлено: [bold]{title}[/bold] ({year}) — ID: {film_id}")
    if status != "unwatched":
        info(f"Статус: {status}")
    # Кинопоиск API не поддерживает синхронизацию watchlist — только локальное хранение


@app.command("list-watchlist")
def list_watchlist(
    status: Optional[str] = typer.Option(
        None, "--status", "-s",
        help="Фильтр по статусу: watched | unwatched | watching",
    ),
    content_type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="Фильтр по типу: movie (фильмы) | tv (сериалы)",
    ),
    sort: str = typer.Option(
        "added", "--sort",
        help="Поле сортировки: added (дата добавления) | priority | rating | title | year",
    ),
    order: str = typer.Option(
        "desc", "--order",
        help="Направление сортировки: desc (убывание) | asc (возрастание)",
    ),
    tag_filter: Optional[str] = typer.Option(
        None, "--tags",
        help="Фильтр по тегам (через запятую). Пример: --tags 'нолан,фантастика'",
    ),
    search_query: Optional[str] = typer.Option(
        None, "--search",
        help="Поиск по названию внутри вашего списка. Пример: --search 'Нолан'",
    ),
    show_stats: bool = typer.Option(
        False, "--stats",
        help="Показать статистику: всего, % просмотрено, средняя оценка",
    ),
    output: str = typer.Option(
        "table", "--output", "-o",
        help="Формат вывода: table (таблица) | json | csv",
    ),
) -> None:
    """📋 Просмотреть свой список фильмов и сериалов.

    Выводит весь watchlist или отфильтрованную часть.
    Весь список хранится локально на вашем компьютере.

    Примеры:
      movie-tracker-claude list-watchlist                          # все записи
      movie-tracker-claude list-watchlist --status unwatched       # только не смотрел
      movie-tracker-claude list-watchlist --status watching        # смотрю сейчас
      movie-tracker-claude list-watchlist --type tv                # только сериалы
      movie-tracker-claude list-watchlist --sort priority          # по приоритету
      movie-tracker-claude list-watchlist --sort rating --order asc
      movie-tracker-claude list-watchlist --tags 'нолан'           # по тегу
      movie-tracker-claude list-watchlist --search 'Начало'        # поиск по названию
      movie-tracker-claude list-watchlist --stats                  # со статистикой
      movie-tracker-claude list-watchlist --output json            # в JSON
    """
    if status and status not in ("watched", "unwatched", "watching"):
        error("Статус: watched | unwatched | watching")
        raise typer.Exit(1)

    if content_type and content_type not in ("movie", "tv"):
        error("Тип: movie | tv")
        raise typer.Exit(1)

    tag_list = parse_tags(tag_filter) if tag_filter else None

    entries, total_count = wl_storage.list_entries(
        status=status,
        media_type=content_type,
        sort_by=sort,
        order=order,
        tags=tag_list,
        search=search_query,
    )

    if not entries:
        if status or content_type or tag_filter or search_query:
            info("Нет записей, соответствующих фильтру.")
        else:
            console.print("[dim]Ваш список пуст. Добавьте первый фильм:[/dim]")
            console.print("  [bold]movie-tracker-claude search 'Интерстеллар'[/bold]")
            console.print("  [bold]movie-tracker-claude add-watchlist <ID>[/bold]")
        return

    print_watchlist(entries, total=total_count, output_format=output)
    if show_stats:
        from movie_tracker.formatters.table import print_watchlist_stats
        stats = wl_storage.get_stats()
        print_watchlist_stats(stats)


# ──────────────────────────────────────────────────────
# watchlist update / remove subcommands
# ──────────────────────────────────────────────────────


@watchlist_app.command("update")
def watchlist_update(
    film_id: int = typer.Argument(..., help="ID записи в watchlist"),
    status: Optional[str] = typer.Option(
        None, "--status", "-s",
        help="Новый статус: watched | unwatched | watching",
    ),
    rating: Optional[float] = typer.Option(
        None, "--rating", "-r",
        help="Оценка от 0.5 до 10.0 (шаг 0.5). Пример: --rating 9.0",
    ),
    note: Optional[str] = typer.Option(
        None, "--note", "-n",
        help="Новая личная заметка. Пример: --note 'Пересмотрел, всё равно круто'",
    ),
    tags: Optional[str] = typer.Option(
        None, "--tags",
        help="Новые теги через запятую. Пример: --tags 'классика,must-see'",
    ),
    priority: Optional[int] = typer.Option(
        None, "--priority",
        help="Новый приоритет от 1 до 5",
        min=1, max=5,
    ),
) -> None:
    """✏️  Обновить запись в watchlist.

    Обновляет статус, оценку, заметку или теги существующей записи.

    Примеры:
      movie-tracker-claude watchlist update 447301 --status watched
      movie-tracker-claude watchlist update 447301 --rating 9.0 --status watched
      movie-tracker-claude watchlist update 447301 --note 'Шедевр' --priority 5
      movie-tracker-claude watchlist update 447301 --tags 'нолан,любимое'
    """
    entry = wl_storage.get_entry(film_id)
    if not entry:
        warning(f"ID {film_id} не найден в watchlist.")
        info("Добавьте командой: movie-tracker-claude add-watchlist " + str(film_id))
        return

    if status and status not in ("watched", "unwatched", "watching"):
        error("Статус: watched | unwatched | watching")
        raise typer.Exit(1)

    validated_rating = None
    if rating is not None:
        try:
            validated_rating = validate_rating(rating)
        except MovieTrackerError as e:
            error(e.message)
            raise typer.Exit(1)

    wl_storage.update_entry(
        film_id,
        status=status,
        rating=validated_rating,
        note=note,
        tags=parse_tags(tags) if tags else None,
        priority=priority,
    )
    success(f"Обновлено: {entry.title} (ID: {film_id})")


@watchlist_app.command("remove")
def watchlist_remove(
    film_id: int = typer.Argument(..., help="ID записи для удаления"),
    force: bool = typer.Option(
        False, "--force", "-f",
        help="Удалить без запроса подтверждения",
    ),
) -> None:
    """🗑  Удалить запись из watchlist.

    По умолчанию запрашивает подтверждение перед удалением.
    Используйте --force для немедленного удаления без вопросов.

    Примеры:
      movie-tracker-claude watchlist remove 447301
      movie-tracker-claude watchlist remove 447301 --force
    """
    entry = wl_storage.get_entry(film_id)
    if not entry:
        warning(f"ID {film_id} не найден в watchlist.")
        return

    if not force:
        confirmed = typer.confirm(
            f"Удалить «{entry.title}» (ID: {film_id}) из watchlist?",
            default=False,
        )
        if not confirmed:
            console.print("[dim]Отменено.[/dim]")
            raise typer.Exit(0)

    wl_storage.remove_entry(film_id)
    success(f"Удалено: {entry.title} (ID: {film_id})")
