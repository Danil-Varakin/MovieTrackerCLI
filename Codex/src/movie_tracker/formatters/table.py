from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from movie_tracker.utils.helpers import display_type, truncate


def media_table(
    console: Console,
    items: list[dict[str, Any]],
    *,
    title: str = "Результаты",
    show_rank: bool = False,
    show_description: bool = False,
) -> None:
    if not items:
        console.print("Ничего не найдено. Попробуйте изменить запрос.", style="yellow")
        return

    table = Table(title=title, box=box.SIMPLE_HEAVY, show_lines=False)
    if show_rank:
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Название", style="bold")
    table.add_column("Тип")
    table.add_column("Год", justify="right")
    table.add_column("Рейтинг", justify="right")
    table.add_column("Жанры")
    if show_description:
        table.add_column("Описание")

    for index, item in enumerate(items, start=1):
        row = [
            str(item.get("id", "")),
            str(item.get("title", "")),
            display_type(item.get("media_type")),
            str(item.get("year") or "-"),
            str(item.get("rating") or "-"),
            ", ".join(item.get("genres", [])[:3]) or "-",
        ]
        if show_rank:
            row.insert(0, str(index))
        if show_description:
            row.append(truncate(item.get("description"), 90) or "-")
        table.add_row(*row)
    console.print(table)


def details_view(console: Console, payload: dict[str, Any]) -> None:
    info = payload.get("info", {})
    raw = payload.get("raw", {})

    lines = [
        f"[bold]{info.get('title')}[/bold] ({info.get('year') or 'год не указан'})",
        f"ID: {info.get('id')} | Тип: {display_type(info.get('media_type'))}",
        f"Кинопоиск: {info.get('rating') or '-'} | IMDb: {info.get('rating_imdb') or '-'}",
        f"Страны: {', '.join(info.get('countries', [])) or '-'}",
        f"Жанры: {', '.join(info.get('genres', [])) or '-'}",
    ]
    if raw.get("filmLength"):
        lines.append(f"Длительность: {raw.get('filmLength')} мин.")
    if raw.get("ratingAgeLimits"):
        lines.append(f"Возрастной рейтинг: {raw.get('ratingAgeLimits')}")
    if raw.get("slogan"):
        lines.append(f"Слоган: {raw.get('slogan')}")
    if raw.get("description"):
        lines.append("")
        lines.append(str(raw.get("description")))

    console.print(Panel("\n".join(lines), title="Информация", expand=False))

    staff = payload.get("staff") or []
    if staff:
        table = Table(title="Съёмочная группа", box=box.SIMPLE)
        table.add_column("Профессия")
        table.add_column("Имя")
        table.add_column("Роль")
        for person in staff[:25]:
            table.add_row(
                str(person.get("professionText") or person.get("professionKey") or "-"),
                str(person.get("nameRu") or person.get("nameEn") or "-"),
                str(person.get("description") or "-"),
            )
        console.print(table)

    reviews = payload.get("reviews") or []
    if reviews:
        table = Table(title="Рецензии", box=box.SIMPLE)
        table.add_column("Автор")
        table.add_column("Тип")
        table.add_column("Дата")
        table.add_column("Текст")
        for review in reviews[:10]:
            table.add_row(
                str(review.get("author") or "-"),
                str(review.get("type") or "-"),
                str(review.get("date") or "-"),
                truncate(review.get("description") or review.get("title"), 120),
            )
        console.print(table)

    similar = payload.get("similar") or []
    if similar:
        media_table(console, similar[:10], title="Похожие", show_description=False)

    seasons = payload.get("seasons") or []
    if seasons:
        table = Table(title="Сезоны", box=box.SIMPLE)
        table.add_column("Сезон", justify="right")
        table.add_column("Эпизодов", justify="right")
        for season in seasons:
            episodes = season.get("episodes") or []
            table.add_row(str(season.get("number") or "-"), str(len(episodes)))
        console.print(table)


def watchlist_table(
    console: Console,
    items: list[dict[str, Any]],
    *,
    stats: dict[str, Any] | None = None,
) -> None:
    if not items:
        console.print(
            "Ваш список пуст. Добавьте фильм: movie-tracker add-watchlist <id>", style="yellow"
        )
    else:
        table = Table(title="Watchlist", box=box.SIMPLE_HEAVY)
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Название", style="bold")
        table.add_column("Тип")
        table.add_column("Статус")
        table.add_column("Оценка", justify="right")
        table.add_column("Приоритет", justify="right")
        table.add_column("Добавлено")
        for item in items:
            table.add_row(
                str(item.get("id")),
                str(item.get("title")),
                display_type(item.get("media_type")),
                str(item.get("status")),
                str(item.get("user_rating") or "-"),
                str(item.get("priority") or "-"),
                str(item.get("added_at") or "-")[:10],
            )
        console.print(table)

    if stats:
        console.print(
            Panel(
                "\n".join(
                    [
                        f"Всего: {stats['total']}",
                        f"Просмотрено: {stats['watched']} ({stats['watched_percent']}%)",
                        f"Смотрю: {stats['watching']}",
                        f"Не просмотрено: {stats['unwatched']}",
                        f"Средняя личная оценка: {stats['average_rating'] or '-'}",
                        "Топ жанров: "
                        + (
                            ", ".join(f"{genre} ({count})" for genre, count in stats["top_genres"])
                            if stats["top_genres"]
                            else "-"
                        ),
                    ]
                ),
                title="Статистика",
                expand=False,
            )
        )
