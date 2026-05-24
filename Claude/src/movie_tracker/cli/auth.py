"""CLI команда: auth — управление API ключом Кинопоиска."""

from __future__ import annotations

import typer
from rich.console import Console

from movie_tracker.formatters.table import error, info, success, warning

app = typer.Typer(help="🔑 Управление API ключом Кинопоиска.")
console = Console()


@app.command("token")
def set_token(
    api_key: str = typer.Argument(..., help="API ключ kinopoiskapiunofficial.tech"),
) -> None:
    """Установить API ключ Кинопоиска."""
    if len(api_key) < 8:
        error("Слишком короткий ключ. Получите бесплатный ключ на: kinopoiskapiunofficial.tech")
        raise typer.Exit(1)

    try:
        from movie_tracker.config import update_setting
        update_setting("api.key", api_key)
        success(f"API ключ сохранён: [dim]{api_key[:4]}***{api_key[-4:]}[/dim]")
        info("Проверьте подключение: [bold]movie-tracker-claude check[/bold]")
    except Exception as e:
        warning(f"Не удалось сохранить в settings.toml: {e}")
        console.print("Задайте через переменную окружения:")
        console.print(f"  [bold]export MOVIE_TRACKER_API__KEY={api_key}[/bold]")


@app.command("status")
def auth_status() -> None:
    """Проверить текущий API ключ."""
    from movie_tracker.config import get_api_key
    api_key = get_api_key()
    if api_key:
        success(f"API ключ установлен: [dim]{api_key[:4]}***{api_key[-4:]}[/dim]")
        info("Проверьте соединение: [bold]movie-tracker-claude check[/bold]")
    else:
        warning("API ключ не установлен.")
        console.print("Установите командой:")
        console.print("  [bold]movie-tracker-claude auth token YOUR_KEY[/bold]")
        console.print()
        console.print("Получить бесплатный ключ: [link=https://kinopoiskapiunofficial.tech]kinopoiskapiunofficial.tech[/link]")


@app.command("login")
def auth_login() -> None:
    """(Не требуется) Кинопоиск API использует только API ключ."""
    info("Кинопоиск API не требует OAuth — достаточно API ключа.")
    console.print("Установите ключ: [bold]movie-tracker-claude auth token YOUR_KEY[/bold]")
    console.print("Получить ключ: [link=https://kinopoiskapiunofficial.tech]kinopoiskapiunofficial.tech[/link]")


@app.command("logout")
def auth_logout() -> None:
    """Удалить сохранённый API ключ."""
    try:
        from movie_tracker.config import update_setting
        update_setting("api.key", "")
        success("API ключ удалён.")
    except Exception as e:
        warning(f"Не удалось очистить ключ: {e}")
        console.print("Удалите вручную из: ~/.movie-tracker/settings.toml")
