from __future__ import annotations

import typer

from movie_tracker.api.client import KinopoiskClient
from movie_tracker.api.details import fetch_details
from movie_tracker.cli.errors import fail
from movie_tracker.cli.state import runtime_from_context
from movie_tracker.exceptions import MovieTrackerError, NotFoundError
from movie_tracker.formatters.output import emit
from movie_tracker.formatters.table import watchlist_table
from movie_tracker.models.movie import MediaItem
from movie_tracker.utils.helpers import parse_tags
from movie_tracker.utils.validators import (
    validate_content_type,
    validate_limit,
    validate_priority,
    validate_rating,
    validate_status,
)

app = typer.Typer(help="Управление локальным watchlist.")


def add_watchlist(
    ctx: typer.Context,
    item_id: int = typer.Argument(..., help="Kinopoisk ID фильма или сериала."),
    content_type: str | None = typer.Option(None, "--type", help="movie | tv; auto по данным API."),
    status: str = typer.Option("unwatched", "--status", help="unwatched | watched | watching"),
    priority: int = typer.Option(3, "--priority", help="Приоритет 1-5."),
    note: str = typer.Option("", "--note", help="Личная заметка."),
    tags: str | None = typer.Option(None, "--tags", help="Теги через запятую."),
) -> None:
    """Добавить фильм или сериал в локальный watchlist."""
    runtime = runtime_from_context(ctx)
    try:
        if content_type:
            validate_content_type(content_type, allow_all=False)
        status = validate_status(status)
        priority = validate_priority(priority)
        client = KinopoiskClient(runtime.config, runtime.auth_store(), runtime.cache())
        payload = fetch_details(client, item_id, section="info")
        item = MediaItem.from_api(payload["raw"])
        record = runtime.watchlist().add(
            item,
            status=status,
            priority=priority,
            note=note,
            tags=parse_tags(tags),
        )
        emit(
            runtime.console,
            runtime.output_format,
            record,
            lambda console, data: console.print(
                f"Добавлено в watchlist: [bold]{data['title']}[/bold] (ID: {data['id']})",
                style="green",
            ),
        )
    except MovieTrackerError as exc:
        fail(runtime, exc)


def list_watchlist(
    ctx: typer.Context,
    status: str = typer.Option("all", "--status", help="watched | unwatched | watching | all"),
    content_type: str = typer.Option("all", "--type", help="movie | tv | all"),
    sort: str = typer.Option("added", "--sort", help="added | priority | rating | title | year"),
    order: str = typer.Option("desc", "--order", help="asc | desc"),
    tags: str | None = typer.Option(None, "--tags", help="Фильтр по тегам."),
    search: str | None = typer.Option(None, "--search", help="Поиск по названию."),
    page: int = typer.Option(1, "--page", help="Номер страницы."),
    stats: bool = typer.Option(False, "--stats", help="Показать статистику."),
) -> None:
    """Показать локальный watchlist."""
    runtime = runtime_from_context(ctx)
    try:
        if status != "all":
            status = validate_status(status)
        content_type = validate_content_type(content_type)
        if sort not in {"added", "priority", "rating", "title", "year"}:
            raise MovieTrackerError("Сортировка: added | priority | rating | title | year")
        if order not in {"asc", "desc"}:
            raise MovieTrackerError("Направление сортировки: asc | desc")
        validate_limit(page, minimum=1, maximum=100000)

        store = runtime.watchlist()
        rows = store.list(
            status=status,
            content_type=content_type,
            tags=parse_tags(tags),
            search=search,
            sort=sort,
            order=order,
        )
        page_size = int(runtime.config.data["output"].get("page_size", 10))
        start = (page - 1) * page_size
        visible_rows = rows[start : start + page_size]
        payload = {"items": visible_rows, "stats": store.stats() if stats else None}
        emit(
            runtime.console,
            runtime.output_format,
            payload,
            lambda console, data: watchlist_table(console, data["items"], stats=data["stats"]),
        )
    except MovieTrackerError as exc:
        fail(runtime, exc)


@app.command("update")
def update(
    ctx: typer.Context,
    item_id: int = typer.Argument(..., help="Kinopoisk ID."),
    status: str | None = typer.Option(None, "--status", help="watched | unwatched | watching"),
    rating: float | None = typer.Option(None, "--rating", help="Личная оценка 0.5-10.0."),
    note: str | None = typer.Option(None, "--note", help="Заметка."),
    tags: str | None = typer.Option(None, "--tags", help="Теги через запятую."),
) -> None:
    """Обновить запись watchlist."""
    runtime = runtime_from_context(ctx)
    try:
        changes: dict[str, object] = {}
        if status is not None:
            changes["status"] = validate_status(status)
        if rating is not None:
            changes["user_rating"] = validate_rating(rating)
            changes.setdefault("status", "watched")
        if note is not None:
            changes["note"] = note
        if tags is not None:
            changes["tags"] = parse_tags(tags)
        record = runtime.watchlist().update(item_id, **changes)
        emit(
            runtime.console,
            runtime.output_format,
            record,
            lambda console, data: console.print(
                f"Обновлено: [bold]{data['title']}[/bold] (ID: {data['id']})",
                style="green",
            ),
        )
    except MovieTrackerError as exc:
        fail(runtime, exc)


@app.command("remove")
def remove(
    ctx: typer.Context,
    item_id: int = typer.Argument(..., help="Kinopoisk ID."),
    force: bool = typer.Option(False, "--force", help="Удалить без подтверждения."),
) -> None:
    """Удалить запись из watchlist."""
    runtime = runtime_from_context(ctx)
    try:
        existing = runtime.watchlist().get(item_id)
        if not existing:
            raise NotFoundError(f"Запись с Kinopoisk ID {item_id} не найдена в watchlist.")
        if not force and not typer.confirm(f"Удалить '{existing['title']}' из watchlist?"):
            runtime.console.print("Удаление отменено.", style="yellow")
            return
        runtime.watchlist().remove(item_id)
        emit(
            runtime.console,
            runtime.output_format,
            {"removed": item_id},
            lambda console, data: console.print(
                f"Удалено из watchlist: ID {data['removed']}", style="green"
            ),
        )
    except MovieTrackerError as exc:
        fail(runtime, exc)


def rate(
    ctx: typer.Context,
    item_id: int = typer.Argument(..., help="Kinopoisk ID."),
    rating: float = typer.Argument(..., help="Оценка от 0.5 до 10.0 с шагом 0.5."),
    content_type: str | None = typer.Option(
        None, "--type", help="movie | tv; оставлено для совместимости."
    ),
    local_only: bool = typer.Option(
        True, "--local-only", help="Kinopoisk API поддерживает только локальное сохранение."
    ),
    review: str | None = typer.Option(None, "--review", help="Личный отзыв."),
) -> None:
    """Поставить локальную оценку и отметить запись просмотренной."""
    runtime = runtime_from_context(ctx)
    try:
        validate_rating(rating)
        if content_type:
            validate_content_type(content_type, allow_all=False)
        store = runtime.watchlist()
        if not store.get(item_id):
            client = KinopoiskClient(runtime.config, runtime.auth_store(), runtime.cache())
            payload = fetch_details(client, item_id, section="info")
            store.add(MediaItem.from_api(payload["raw"]), status="watched")
        record = store.rate(item_id, rating, review=review)
        if not local_only and not runtime.quiet:
            runtime.console.print(
                "Kinopoisk API Unofficial не принимает пользовательские оценки; оценка сохранена локально.",
                style="yellow",
            )
        emit(
            runtime.console,
            runtime.output_format,
            record,
            lambda console, data: console.print(
                f"Оценка сохранена: [bold]{data['title']}[/bold] — {data['user_rating']}",
                style="green",
            ),
        )
    except MovieTrackerError as exc:
        fail(runtime, exc)
