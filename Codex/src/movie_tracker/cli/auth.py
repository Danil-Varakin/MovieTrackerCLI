from __future__ import annotations

import typer

from movie_tracker.cli.state import runtime_from_context
from movie_tracker.formatters.output import emit
from movie_tracker.utils.helpers import masked_secret

app = typer.Typer(help="API-ключ Kinopoisk API Unofficial.")


@app.command("login")
def login(ctx: typer.Context) -> None:
    """Показать корректный способ авторизации для Kinopoisk API."""
    runtime = runtime_from_context(ctx)
    runtime.console.print(
        "Kinopoisk API Unofficial не предоставляет OAuth-login. "
        "Используйте: movie-tracker auth token YOUR_KINOPOISK_API_KEY",
        style="yellow",
    )


@app.command("logout")
def logout(ctx: typer.Context) -> None:
    """Удалить сохранённый локальный API-ключ."""
    runtime = runtime_from_context(ctx)
    removed = runtime.auth_store().clear()
    message = "Сохранённый API-ключ удалён." if removed else "Сохранённый API-ключ не найден."
    runtime.console.print(message, style="green" if removed else "yellow")


@app.command("status")
def status(ctx: typer.Context) -> None:
    """Показать статус локального API-ключа."""
    runtime = runtime_from_context(ctx)
    auth_status = runtime.auth_store().status()
    config_key = runtime.config.api_key
    payload = {
        **auth_status,
        "config_or_env_key": bool(config_key),
        "config_or_env_masked": masked_secret(config_key),
    }
    emit(
        runtime.console,
        runtime.output_format,
        payload,
        lambda console, data: console.print(
            "\n".join(
                [
                    "Kinopoisk API Unofficial",
                    f"Локальный ключ: {'есть' if data['authorized'] else 'нет'}",
                    f"Ключ из env/config: {'есть' if data['config_or_env_key'] else 'нет'}",
                    f"Маска: {data['config_or_env_masked'] or data['masked_key'] or '-'}",
                    f"Файл: {data['path']}",
                ]
            )
        ),
    )


@app.command("token")
def token(
    ctx: typer.Context,
    api_key: str = typer.Argument(..., help="API-ключ Kinopoisk API Unofficial."),
) -> None:
    """Сохранить API-ключ локально."""
    runtime = runtime_from_context(ctx)
    runtime.auth_store().save_api_key(api_key)
    runtime.console.print(
        f"API-ключ сохранён: {masked_secret(api_key)}",
        style="green",
    )
