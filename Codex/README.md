# MovieTracker CLI Codex

Консольная утилита для поиска фильмов и сериалов, локального watchlist, оценок и рекомендаций. Эта версия реализована под **Kinopoisk API Unofficial** вместо TMDB и устанавливается как обычная команда `movie-tracker`.

## Быстрый старт

```bash
python -m pip install .
movie-tracker init
movie-tracker auth token YOUR_KINOPOISK_API_KEY
movie-tracker search "Матрица"
```

Ключ можно получить на сайте [Kinopoisk API Unofficial](https://api.kinopoiskapiunofficial.tech/).

## Основные команды

```bash
movie-tracker search "Бойцовский клуб" --type movie
movie-tracker details 361 --section all
movie-tracker add-watchlist 361 --priority 5 --tags "драма,классика"
movie-tracker list-watchlist --stats
movie-tracker rate 361 9.5 --review "Сильное кино"
movie-tracker recommend --based-on 361 --limit 5
movie-tracker popular --type movie --limit 10
movie-tracker trending --window week
```

## Разработка

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e ".[dev]"
movie-tracker --help
```

## Тестирование

```bash
pytest
pytest --cov=movie_tracker --cov-report=term-missing
ruff check src tests
mypy src
```

Подробное описание именно этой версии находится в [MOVIETRACKER_CLI_CODEX_VERSION.md](MOVIETRACKER_CLI_CODEX_VERSION.md).
