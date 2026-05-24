"""Форматтеры вывода — Rich таблицы, JSON, CSV."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from movie_tracker.config import get_color
from movie_tracker.models import (
    Credits,
    MovieDetails,
    Review,
    SearchPage,
    SearchResult,
    TVDetails,
    WatchlistEntry,
    WatchlistStats,
)

console = Console(highlight=False, no_color=not get_color())
err_console = Console(stderr=True, style="bold red")


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def _stars(rating: float) -> str:
    """Визуализирует рейтинг через звёзды/цвет."""
    if rating >= 8.0:
        return f"[green]{rating:.1f}[/green] ⭐"
    elif rating >= 6.0:
        return f"[yellow]{rating:.1f}[/yellow]"
    elif rating > 0:
        return f"[red]{rating:.1f}[/red]"
    return "[dim]—[/dim]"


def _status_badge(status: str) -> str:
    badges = {
        "watched": "[green]✓ Просмотрено[/green]",
        "watching": "[yellow]▶ Смотрю[/yellow]",
        "unwatched": "[dim]○ Не смотрел[/dim]",
    }
    return badges.get(status, status)


def _priority_bar(priority: int) -> str:
    filled = "█" * priority
    empty = "░" * (5 - priority)
    colors = {1: "dim", 2: "blue", 3: "cyan", 4: "yellow", 5: "red"}
    color = colors.get(priority, "white")
    return f"[{color}]{filled}{empty}[/{color}]"


def _truncate(text: str, length: int = 50) -> str:
    return text if len(text) <= length else text[: length - 1] + "…"


def _format_money(amount: int) -> str:
    if amount == 0:
        return "—"
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    return f"${amount:,}"


# ─────────────────────────────────────────────────────────────
# Search Results
# ─────────────────────────────────────────────────────────────


def print_search_results(
    page: SearchPage,
    genre_map: dict[int, str] | None = None,
    output_format: str = "table",
) -> None:
    if not page.results:
        console.print(
            "\n[yellow]Ничего не найдено. Попробуйте изменить запрос.[/yellow]\n"
        )
        return

    if output_format == "json":
        _print_json_results(page)
    elif output_format == "csv":
        _print_csv_results(page, genre_map)
    else:
        _print_table_results(page, genre_map)


def _print_table_results(
    page: SearchPage, genre_map: dict[int, str] | None = None
) -> None:
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        title=f"[bold]Результаты поиска[/bold] (страница {page.page}/{page.total_pages}, всего: {page.total_results})",
        title_style="bold white",
        expand=True,
    )
    table.add_column("ID", style="dim", width=8, justify="right")
    table.add_column("Название", min_width=25, max_width=40)
    table.add_column("Тип", width=8)
    table.add_column("Год", width=6, justify="center")
    table.add_column("Рейтинг", width=12, justify="center")
    table.add_column("Жанры", min_width=20, max_width=30)

    for r in page.results:
        media_label = "[blue]Фильм[/blue]" if r.media_type == "movie" else "[magenta]Сериал[/magenta]"
        # Кинопоиск: жанры хранятся как текст в genre_names, не как ID
        genres = getattr(r, "genre_names_str", "") or ""
        if not genres and genre_map and r.genre_ids:
            genre_names = [genre_map.get(gid, "") for gid in r.genre_ids[:3]]
            genres = ", ".join(g for g in genre_names if g)

        table.add_row(
            str(r.id),
            _truncate(r.title, 38),
            media_label,
            r.year,
            _stars(r.vote_average) if r.vote_average else "[dim]—[/dim]",
            genres or "[dim]—[/dim]",
        )

    console.print(table)
    if page.total_pages > 1:
        console.print(
            f"[dim]  Страница {page.page} из {page.total_pages}. "
            f"Используйте --page для навигации.[/dim]"
        )


def _print_json_results(page: SearchPage) -> None:
    data = {
        "page": page.page,
        "total_pages": page.total_pages,
        "total_results": page.total_results,
        "results": [
            {
                "id": r.id,
                "type": r.media_type,
                "title": r.title,
                "year": r.year,
                "rating": r.vote_average,
                "popularity": r.popularity,
            }
            for r in page.results
        ],
    }
    console.print_json(json.dumps(data, ensure_ascii=False))


def _print_csv_results(
    page: SearchPage, genre_map: dict[int, str] | None = None
) -> None:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Тип", "Название", "Год", "Рейтинг", "Жанры"])
    for r in page.results:
        genres = ""
        if genre_map and r.genre_ids:
            genres = "; ".join(genre_map.get(g, str(g)) for g in r.genre_ids[:3])
        writer.writerow(
            [r.id, r.media_type, r.title, r.year, r.vote_average, genres]
        )
    console.print(output.getvalue())


# ─────────────────────────────────────────────────────────────
# Movie Details
# ─────────────────────────────────────────────────────────────


def print_movie_details(movie: MovieDetails) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold yellow]{movie.title}[/bold yellow]"
            + (f"\n[dim]{movie.original_title}[/dim]" if movie.original_title != movie.title else "")
            + (f"\n[italic dim]{movie.tagline}[/italic dim]" if movie.tagline else ""),
            title="[bold]🎬 Фильм[/bold]",
            border_style="yellow",
            expand=False,
        )
    )

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold dim", width=18)
    grid.add_column()

    genre_names = ", ".join(g.name for g in movie.genres) or "—"
    grid.add_row("📅 Дата выхода:", movie.release_date or "—")
    grid.add_row("⏱ Длительность:", f"{movie.runtime} мин." if movie.runtime else "—")
    grid.add_row("🎭 Жанры:", genre_names)
    grid.add_row("⭐ Кинопоиск рейтинг:", f"{movie.vote_average:.1f} / 10 ({movie.vote_count:,} голосов)")
    grid.add_row("🆔 IMDB:", movie.imdb_id or "—")
    grid.add_row("🌍 Страна:", ", ".join(movie.production_countries) or "—")
    grid.add_row("💰 Бюджет:", _format_money(movie.budget))
    grid.add_row("💵 Сборы:", _format_money(movie.revenue))
    grid.add_row("📊 Статус:", movie.status or "—")

    console.print(grid)

    if movie.overview:
        console.print()
        console.print(Panel(
            movie.overview,
            title="[bold]Описание[/bold]",
            border_style="dim",
            expand=True,
        ))
    console.print()


def print_tv_details(tv: TVDetails) -> None:
    console.print()
    status_color = "green" if tv.in_production else "dim"
    console.print(
        Panel(
            f"[bold magenta]{tv.name}[/bold magenta]"
            + (f"\n[dim]{tv.original_name}[/dim]" if tv.original_name != tv.name else "")
            + (f"\n[italic dim]{tv.tagline}[/italic dim]" if tv.tagline else ""),
            title="[bold]📺 Сериал[/bold]",
            border_style="magenta",
            expand=False,
        )
    )

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold dim", width=20)
    grid.add_column()

    genre_names = ", ".join(g.name for g in tv.genres) or "—"
    grid.add_row("📅 Первый эпизод:", tv.first_air_date or "—")
    grid.add_row("📅 Последний эпизод:", tv.last_air_date or "—")
    grid.add_row("📼 Сезонов:", str(tv.number_of_seasons))
    grid.add_row("🎞 Эпизодов:", str(tv.number_of_episodes))
    grid.add_row("🎭 Жанры:", genre_names)
    grid.add_row("⭐ Кинопоиск рейтинг:", f"{tv.vote_average:.1f} / 10 ({tv.vote_count:,} голосов)")
    grid.add_row("📡 Сеть:", ", ".join(tv.networks) or "—")
    grid.add_row("🌍 Страна:", ", ".join(tv.origin_country) or "—")
    grid.add_row(f"[{status_color}]📊 Статус:[/{status_color}]", f"[{status_color}]{tv.status}[/{status_color}]")

    console.print(grid)

    if tv.overview:
        console.print()
        console.print(Panel(
            tv.overview,
            title="[bold]Описание[/bold]",
            border_style="dim",
            expand=True,
        ))
    console.print()


# ─────────────────────────────────────────────────────────────
# Credits
# ─────────────────────────────────────────────────────────────


def print_credits(credits: Credits) -> None:
    if credits.directors:
        console.print("\n[bold]🎬 Режиссёры:[/bold]")
        for d in credits.directors:
            console.print(f"  • {d.name}")

    if credits.writers:
        console.print("\n[bold]✍️  Сценаристы:[/bold]")
        for w in credits.writers[:5]:
            console.print(f"  • {w.name} ({w.job})")

    if credits.cast:
        console.print("\n[bold]🎭 Актёрский состав:[/bold]")
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        table.add_column("#", width=4, justify="right", style="dim")
        table.add_column("Актёр", min_width=20)
        table.add_column("Персонаж", min_width=20)

        for member in credits.cast[:20]:
            table.add_row(
                str(member.order + 1),
                member.name,
                member.character or "—",
            )
        console.print(table)


# ─────────────────────────────────────────────────────────────
# Reviews
# ─────────────────────────────────────────────────────────────


def print_reviews(reviews: list[Review], page: int, total_pages: int) -> None:
    if not reviews:
        console.print("[yellow]Рецензии отсутствуют.[/yellow]")
        return

    console.print(f"\n[bold]📝 Рецензии[/bold] (страница {page}/{total_pages})\n")
    for r in reviews:
        rating_str = f"  [{_stars(r.rating)}]" if r.rating else ""
        console.print(
            Panel(
                _truncate(r.content, 400),
                title=f"[bold]{r.author}[/bold]{rating_str}  [dim]{r.created_at}[/dim]",
                border_style="dim",
                expand=True,
            )
        )


# ─────────────────────────────────────────────────────────────
# Watchlist
# ─────────────────────────────────────────────────────────────


def print_watchlist(
    entries: list[WatchlistEntry],
    total: int,
    page: int = 1,
    output_format: str = "table",
) -> None:
    if not entries and total == 0:
        console.print(
            "\n[yellow]Ваш список пуст. Добавьте фильм:[/yellow] "
            "[bold]movie-tracker-claude add-watchlist <id>[/bold]\n"
        )
        return

    if output_format == "json":
        data = [e.to_dict() for e in entries]
        console.print_json(json.dumps(data, ensure_ascii=False, default=str))
        return

    table = Table(
        box=box.ROUNDED,
        header_style="bold cyan",
        title=f"[bold]📋 Мой список[/bold] (всего: {total})",
        expand=True,
    )
    table.add_column("ID", style="dim", width=8, justify="right")
    table.add_column("Название", min_width=25, max_width=35)
    table.add_column("Тип", width=8)
    table.add_column("Год", width=6, justify="center")
    table.add_column("Статус", min_width=16)
    table.add_column("Оценка", width=8, justify="center")
    table.add_column("Приоритет", width=10, justify="center")
    table.add_column("Добавлено", width=12)

    for e in entries:
        media_label = "[blue]Фильм[/blue]" if e.media_type == "movie" else "[magenta]Сериал[/magenta]"
        rating_str = f"[cyan]{e.rating:.1f}[/cyan]" if e.rating else "[dim]—[/dim]"
        added = e.added_at[:10] if e.added_at else "—"

        table.add_row(
            str(e.film_id),
            _truncate(e.title, 33),
            media_label,
            e.year,
            _status_badge(e.status),
            rating_str,
            _priority_bar(e.priority),
            added,
        )

    console.print(table)


def print_watchlist_stats(stats: WatchlistStats) -> None:
    console.print()
    grid = Table.grid(padding=(0, 3))
    grid.add_column(style="bold")
    grid.add_column(justify="right")

    grid.add_row("📊 Всего записей:", str(stats.total))
    grid.add_row("[green]✓ Просмотрено:[/green]", f"{stats.watched} ({stats.watched_percent}%)")
    grid.add_row("[yellow]▶ Смотрю:[/yellow]", str(stats.watching))
    grid.add_row("[dim]○ Не смотрел:[/dim]", str(stats.unwatched))
    grid.add_row("[blue]🎬 Фильмов:[/blue]", str(stats.movies))
    grid.add_row("[magenta]📺 Сериалов:[/magenta]", str(stats.tv_shows))

    if stats.avg_rating is not None:
        grid.add_row(
            "⭐ Средняя оценка:",
            f"{stats.avg_rating:.2f} (из {stats.rated_count} оценённых)",
        )

    console.print(Panel(grid, title="[bold]📈 Статистика watchlist[/bold]", border_style="cyan"))
    console.print()


# ─────────────────────────────────────────────────────────────
# Popular / Trending
# ─────────────────────────────────────────────────────────────


def print_popular(
    page: SearchPage,
    offset: int = 0,
    genre_map: dict[int, str] | None = None,
    output_format: str = "table",
) -> None:
    if output_format == "json":
        _print_json_results(page)
        return

    table = Table(
        box=box.ROUNDED,
        header_style="bold cyan",
        title="[bold]🔥 Популярное[/bold]",
        expand=True,
    )
    table.add_column("Место", width=6, justify="center")
    table.add_column("ID", style="dim", width=8, justify="right")
    table.add_column("Название", min_width=25, max_width=40)
    table.add_column("Год", width=6, justify="center")
    table.add_column("Рейтинг", width=12, justify="center")
    table.add_column("Голоса", width=10, justify="right")
    table.add_column("Жанры", min_width=20, max_width=25)

    for i, r in enumerate(page.results, start=offset + 1):
        genres = ""
        if genre_map and r.genre_ids:
            genres = ", ".join(genre_map.get(g, "") for g in r.genre_ids[:3] if genre_map.get(g))

        table.add_row(
            f"[bold]{i}[/bold]",
            str(r.id),
            _truncate(r.title, 38),
            r.year,
            _stars(r.vote_average),
            f"{r.vote_count:,}",
            genres or "—",
        )

    console.print(table)


def print_trending(
    page: SearchPage,
    window: str = "day",
    genre_map: dict[int, str] | None = None,
    output_format: str = "table",
) -> None:
    if output_format == "json":
        _print_json_results(page)
        return

    period_label = "за день" if window == "day" else "за неделю"
    table = Table(
        box=box.ROUNDED,
        header_style="bold cyan",
        title=f"[bold]📈 В тренде {period_label}[/bold]",
        expand=True,
    )
    table.add_column("Место", width=6, justify="center")
    table.add_column("ID", style="dim", width=8, justify="right")
    table.add_column("Название", min_width=25, max_width=40)
    table.add_column("Тип", width=8)
    table.add_column("Год", width=6, justify="center")
    table.add_column("Рейтинг", width=12, justify="center")

    for i, r in enumerate(page.results, start=1):
        media_label = "[blue]Фильм[/blue]" if r.media_type == "movie" else "[magenta]Сериал[/magenta]"
        table.add_row(
            f"[bold yellow]{i}[/bold yellow]",
            str(r.id),
            _truncate(r.title, 38),
            media_label,
            r.year,
            _stars(r.vote_average),
        )

    console.print(table)


# ─────────────────────────────────────────────────────────────
# Messages
# ─────────────────────────────────────────────────────────────


def success(msg: str) -> None:
    console.print(f"[bold green]✓[/bold green] {msg}")


def warning(msg: str) -> None:
    console.print(f"[bold yellow]⚠[/bold yellow] {msg}")


def error(msg: str) -> None:
    err_console.print(f"[bold red]✗[/bold red] {msg}")


def info(msg: str) -> None:
    console.print(f"[bold cyan]ℹ[/bold cyan] {msg}")
